"""
Pose Actions Module.

This module provides the PoseActionsMixin class, which handles pose recognition,
scanning for pose requests, and managing pose-related actions in the chatbot.
It includes image processing for pose identification and screenshot saving.

Classes:
    PoseActionsMixin: Mixin class for pose actions and recognition.
"""

import asyncio
import pyautogui
import time
import os
import cv2
import numpy as np
import concurrent.futures
import hashlib
from .config import ACCEPT_POSE_IMAGE_PATH, POSES_DIR, UNKNOWN_POSES_DIR, GIFT_IMAGE_PATH
from .utils import extract_text_from_image


class PoseActionsMixin:
    """
    Mixin class for handling pose-related actions.

    This mixin provides methods for automated pose recognition using computer vision,
    scanning for pose change requests, accepting poses, and saving unknown poses
    for later classification.

    Methods:
        crop_to_content: Crop image to main content area.
        _normalize_image_for_matching: Normalize image for pose matching.
        _get_pose_name: Get pose name from current pose icon.
        _process_pose_matching: Process pose matching against database.
        _save_unknown_pose_screenshot: Save screenshot of unknown pose.
        _scan_for_poses: Scan for pose change requests.
    """

    def crop_to_content(self, img_gray):
        """
        Smart cropping to content area.

        Uses contour detection to find the largest object and ignore small noise.
        Adds padding to avoid cutting off content.

        Args:
            img_gray (numpy.ndarray): Grayscale image to crop.

        Returns:
            numpy.ndarray or None: Cropped image or None if no content found.
        """
        # 1. Binarization (black/white)
        # Threshold 25 ok, but can add light blur to remove noise
        blurred = cv2.GaussianBlur(img_gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 25, 255, cv2.THRESH_BINARY)

        # 2. Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None  # Empty image

        # 3. Find the largest contour (this is our pose)
        # This protects against small noise dots in zone corners
        main_contour = max(contours, key=cv2.contourArea)

        # 4. Get rectangle coordinates around contour
        x, y, w, h = cv2.boundingRect(main_contour)

        # Add small padding (margin) to avoid cutting off content
        pad = 2
        h_img, w_img = img_gray.shape
        y1 = max(0, y - pad)
        y2 = min(h_img, y + h + pad)
        x1 = max(0, x - pad)
        x2 = min(w_img, x + w + pad)

        return img_gray[y1:y2, x1:x2]

    def _normalize_image_for_matching(self, img, target_height=100):
        """
        Normalize image to standard height while preserving aspect ratio.

        This allows comparing poses from different screen resolutions (4K vs 1080p).

        Args:
            img (numpy.ndarray): Image to normalize.
            target_height (int): Target height in pixels. Defaults to 100.

        Returns:
            numpy.ndarray or None: Normalized image or None if invalid.
        """
        if img is None: return None
        h, w = img.shape[:2]
        if h == 0 or w == 0: return None
        
        scale = target_height / float(h)
        target_width = int(w * scale)
        
        resized = cv2.resize(img, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
        return resized

    async def _get_pose_name(self):
        """
        Get pose name from current pose icon.

        Captures screenshot of pose icon area, processes it, and matches against
        known poses database.

        Returns:
            tuple: (pose_name, screenshot) where pose_name is recognized pose
                   or "unknown pose", and screenshot is the captured image.
        """
        area = self.areas.get('pose_icon_area')
        if not area:
            self.log("pose_icon_area not configured", internal=True)
            return "unknown pose", None
        
        try:
            # Take screenshot
            region_screenshot = pyautogui.screenshot(region=(area['x'], area['y'], area['width'], area['height']))
            test_img = np.array(region_screenshot)
            test_gray = cv2.cvtColor(test_img, cv2.COLOR_RGB2GRAY)

            # IMPORTANT: Crop first to remove extra background
            cropped_test = self.crop_to_content(test_gray)

            if cropped_test is None:
                return "empty", region_screenshot

            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Pass already cropped image
                result = await loop.run_in_executor(executor, self._process_pose_matching, cropped_test)

            best_match, best_confidence = result

            # Confidence threshold. For matchTemplate 0.8 is usually reliable.
            if best_match and best_confidence > 0.8:
                pose_name = os.path.splitext(best_match)[0]
                self.log(f"Pose: {pose_name} ({best_confidence:.2f})", internal=False)
                return pose_name, region_screenshot  # Return full screenshot for logs
            else:
                self.log(f"Pose not recognized (max: {best_confidence:.2f})", internal=False)
                # Return cropped_test in tuple or separately if need to save crop specifically
                # But logic below expects region_screenshot for saving, we crop it ourselves in save
                return "unknown pose", region_screenshot

        except Exception as e:
            self.log(f"Error scanning pose: {e}", internal=True)
            return "unknown pose", None

    def _process_pose_matching(self, cropped_test):
        """
        Process pose matching against database.

        Comparison logic:
        1. Normalize test image to 100px height.
        2. Iterate through database.
        3. Normalize database image to 100px height.
        4. Compare images.

        Args:
            cropped_test (numpy.ndarray): Cropped test image.

        Returns:
            tuple: (best_match_filename, best_confidence)
        """
        best_match = None
        best_confidence = 0.0
        
        # Normalize input test to standard height
        norm_test = self._normalize_image_for_matching(cropped_test, target_height=100)
        if norm_test is None: return None, 0.0

        for root, dirs, files in os.walk(POSES_DIR):
            for filename in files:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(root, filename)
                    try:
                        # Read directly in Gray
                        pose_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                        if pose_img is None: continue

                        # 1. Crop database (in case uncropped images are saved there)
                        cropped_pose = self.crop_to_content(pose_img)

                        # 2. Normalize database to SAME height (100px)
                        norm_pose = self._normalize_image_for_matching(cropped_pose, target_height=100)

                        if norm_pose is None: continue

                        # 3. Aspect Ratio Check
                        # If widths differ significantly after normalization, these are different poses
                        # For example, "standing" pose (narrow) and "lying" pose (wide)
                        w_test = norm_test.shape[1]
                        w_pose = norm_pose.shape[1]

                        # Allow 15% width difference (different fonts, rendering nuances)
                        if abs(w_test - w_pose) / w_pose > 0.15:
                            continue

                        # 4. Final size adjustment for matchTemplate
                        # matchTemplate requires template to be <= source.
                        # Here they are approximately equal. Force resize pose to test
                        # Since we already checked proportions, distortion will be minimal
                        final_pose = cv2.resize(norm_pose, (w_test, 100))

                        # 5. Comparison
                        res = cv2.matchTemplate(norm_test, final_pose, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(res)

                        if max_val > best_confidence:
                            best_confidence = max_val
                            best_match = filename

                    except Exception:
                        continue

        return best_match, best_confidence

    async def _save_unknown_pose_screenshot(self, screenshot_img):
        """
        Save only UNIQUE CROPPED content.

        This prevents duplicates due to different capture sizes.

        Args:
            screenshot_img: Screenshot image to save.
        """
        try:
            os.makedirs(UNKNOWN_POSES_DIR, exist_ok=True)

            # 1. Convert original screenshot
            test_img = np.array(screenshot_img)
            test_gray = cv2.cvtColor(test_img, cv2.COLOR_RGB2GRAY)

            # 2. CROP before hashing!
            # This is key: we hash the essence, not black fields
            cropped_img = self.crop_to_content(test_gray)

            if cropped_img is None:
                return

            # 3. Hash bytes of cropped image
            img_bytes = cropped_img.tobytes()
            img_hash = hashlib.md5(img_bytes).hexdigest()

            # Check for existence by hash (can check by filename if adding hash to name)
            # For reliability can iterate through folder and compare content, but hash name search is faster

            # Look for file with this hash in name
            existing_files = [f for f in os.listdir(UNKNOWN_POSES_DIR) if img_hash in f]
            if existing_files:
                self.log(f"Pose already exists in unknown (hash match): {existing_files[0]}", internal=True)
                return

            # 4. Save EXACTLY the CROPPED image
            # This will make manual labeling easier later - no need to crop yourself
            timestamp = int(time.time())
            filename = f"pose_{timestamp}_{img_hash[:8]}.png"
            filepath = os.path.join(UNKNOWN_POSES_DIR, filename)

            cv2.imwrite(filepath, cropped_img)
            self.log(f"Saved new pose: {filename}", internal=True)

        except Exception as e:
            self.log(f"Error saving unknown: {e}", internal=True)

    async def _save_named_pose_screenshot(self, pose_name, screenshot_img):
        """
        Save the pose screenshot to the named folder with the provided name.

        Args:
            pose_name (str): The name for the pose.
            screenshot_img: Screenshot image to save.
        """
        try:
            from .config import POSES_DIR
            unnamed_dir = os.path.join(POSES_DIR, "unnamed")
            os.makedirs(unnamed_dir, exist_ok=True)

            # Convert original screenshot
            test_img = np.array(screenshot_img)
            test_gray = cv2.cvtColor(test_img, cv2.COLOR_RGB2GRAY)

            # Crop
            cropped_img = self.crop_to_content(test_gray)

            if cropped_img is None:
                return

            # Sanitize pose_name for filename
            safe_name = "".join('_' if c in '<>:"|?*\\/' else c for c in pose_name).strip()
            if len(safe_name) > 200:
                safe_name = safe_name[:200]

            # Check if file already exists
            filepath = os.path.join(unnamed_dir, f"{safe_name}.png")
            if os.path.exists(filepath):
                self.log(f"Pose '{safe_name}' already exists, not overwriting.", internal=True)
                return

            cv2.imwrite(filepath, cropped_img)
            self.log(f"Saved named pose: {safe_name}.png", internal=True)

        except Exception as e:
            self.log(f"Error saving named pose: {e}", internal=True)

    async def _scan_for_poses(self):
        """
        Scan for pose change requests.

        Searches for accept buttons in pose area, recognizes pose name,
        accepts the pose, and sends notification message.
        """
        area = self.areas.get('pose_area')
        if not area: return

        # Cooldown to prevent double-clicks
        if time.time() - self.last_pose_action_time < 3.0:
            return

        try:
            # 1. Search for Accept button image
            if os.path.exists(ACCEPT_POSE_IMAGE_PATH):
                try:
                    location = pyautogui.locateCenterOnScreen(
                        ACCEPT_POSE_IMAGE_PATH,
                        region=(area['x'], area['y'], area['width'], area['height']),
                        confidence=0.8
                    )
                    if location:
                        self.log(f"Pose request found (img): {location}", internal=True)
                        # Scan pose only when accept button is found
                        pose_name, pose_screenshot = await self._get_pose_name()
                        self.log(f"Pose recognized as: {pose_name}", internal=True)
                        pyautogui.mouseDown(location.x, location.y)
                        time.sleep(0.01)
                        pyautogui.mouseUp(location.x, location.y)
                        self.last_message_time = time.time()
                        self.last_pose_action_time = time.time()
                        self.log(f"Clicked accept button for pose scan", internal=True)

                        # Notify bot of pose change with name
                        if pose_name == "unknown pose":
                            self.log(f"Unknown pose detected, waiting for user name", internal=True)
                            message = self.get_unknown_pose_message()
                            self.waiting_for_pose_name = True
                            self.pending_pose_screenshot = pose_screenshot
                            self.pending_accept_location = location  # Store accept button location
                            await self.send_to_game([message])
                            # Don't click accept yet
                        else:
                            self.log(f"Known pose {pose_name}, sending to hiwaifu", internal=True)
                            message = f"{self.get_pose_message()} {pose_name}"
                            self.initiate_chat_from_text(message)

                        await asyncio.sleep(0.5)
                        return
                except Exception as e:
                    pass

            # 2. Fallback OCR
            screenshot = pyautogui.screenshot(region=(area['x'], area['y'], area['width'], area['height']))
            text = extract_text_from_image(screenshot, "en")

            if "accept" in text.lower():
                self.log("Pose request detected (OCR)! Waiting for description...", internal=True)

                # Screenshot pose icon
                icon_screenshot = None
                icon_area = self.areas.get('pose_icon_area')
                if icon_area:
                    icon_screenshot = pyautogui.screenshot(region=(icon_area['x'], icon_area['y'], icon_area['width'], icon_area['height']))

                center_x = area['x'] + area['width'] // 2
                center_y = area['y'] + area['height'] // 2

                # Notify bot of pose change with name
                pose_name = "unknown pose"  # Fallback since pose scanning not done in OCR
                message = self.get_unknown_pose_message()
                self.waiting_for_pose_name = True
                self.pending_pose_screenshot = icon_screenshot
                self.pending_accept_location = pyautogui.Point(center_x, center_y)  # Store the click location
                await self.send_to_game([message])
                # Don't click accept yet

                await asyncio.sleep(0.5)
        except Exception as e:
            pass

    async def _scan_for_gifts(self):
        """
        Scan for gift detection.

        Searches for gift.png image across the entire screen
        and clicks on it when detected, same as accept_clothes_control.png.
        """
        # Cooldown to prevent spam
        current_time = time.time()
        if not hasattr(self, 'last_gift_time'):
            self.last_gift_time = 0
        if current_time - self.last_gift_time < 5.0:  # 5 second cooldown
            return

        try:
            if os.path.exists(GIFT_IMAGE_PATH):
                # Search for gift image across entire screen
                location = pyautogui.locateCenterOnScreen(
                    GIFT_IMAGE_PATH,
                    confidence=0.8
                )

                if location:
                    self.log(f"Gift detected at {location}", internal=True)

                    # Click on center of gift
                    self.log(f"Click on gift center: {location.x}, {location.y}", internal=True)
                    pyautogui.mouseDown(location.x, location.y)
                    time.sleep(0.01)
                    pyautogui.mouseUp(location.x, location.y)
                    self.last_gift_time = current_time

                    message = self.get_gift_message()
                    self.initiate_chat_from_text(message)
                    await asyncio.sleep(0.5)
        except Exception as e:
            pass