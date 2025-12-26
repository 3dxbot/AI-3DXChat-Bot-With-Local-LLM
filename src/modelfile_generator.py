"""
Modelfile Generator Module.

This module provides the ModelfileGenerator class for creating and managing
Modelfile configurations for both GGUF and standard Ollama models with
character integration.

Classes:
    ModelfileGenerator: Class for generating Modelfile configurations.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging


class ModelfileGenerator:
    """
    Generator class for Modelfile configurations.
    
    Handles creation of Modelfile for both GGUF and standard models with
    character integration and template management.
    
    Attributes:
        logger: Logger instance for logging operations.
    """
    
    def __init__(self):
        """Initialize ModelfileGenerator."""
        self.logger = logging.getLogger(__name__)
    
    def generate_gguf_modelfile(self, model_name: str, gguf_path: str,
                               system_prompt: str = "", manifest: str = "",
                               model_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate Modelfile for GGUF model with character integration.
        
        Args:
            model_name: Name of the model.
            gguf_path: Path to the GGUF file.
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            model_params: Additional model parameters.
            
        Returns:
            str: Generated Modelfile content.
        """
        # Default model parameters
        default_params = {
            "num_ctx": 4096,
            "num_threads": 4,
            "num_gpu": 1,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        
        # Update with provided parameters
        if model_params:
            default_params.update(model_params)
        
        # Base GGUF model configuration
        modelfile_lines = [
            f"FROM {gguf_path}",
            f"# Modelfile for {model_name}",
            f"# Generated from GGUF file: {gguf_path}",
            "",
            "# Model parameters",
        ]
        
        # Add model parameters
        for param, value in default_params.items():
            modelfile_lines.append(f"PARAMETER {param} {value}")
        
        modelfile_lines.append("")
        
        # Add system prompt if provided
        if system_prompt.strip():
            modelfile_lines.extend([
                "# System prompt from character",
                f"SYSTEM \"\"\"",
                system_prompt,
                "\"\"\"",
                "",
            ])
        
        # Add character context and template
        if manifest.strip():
            modelfile_lines.extend([
                "# Character context and conversation template",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "",
                "## Character Information",
                manifest,
                "",
                "## Conversation Rules",
                "- Always respond in character",
                "- Maintain consistent personality traits",
                "- Use appropriate language and tone",
                "- Remember previous interactions",
                "",
                "## Current Conversation",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        else:
            # Default template if no character context
            modelfile_lines.extend([
                "# Default conversation template",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        
        return "\n".join(modelfile_lines)
    
    def generate_standard_modelfile(self, model_name: str, base_model: str,
                                   system_prompt: str = "", manifest: str = "",
                                   model_params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate Modelfile for standard Ollama model with character integration.
        
        Args:
            model_name: Name of the model.
            base_model: Base model name (e.g., "llama2", "mistral").
            system_prompt: System prompt from character.
            manifest: Character manifest info.
            model_params: Additional model parameters.
            
        Returns:
            str: Generated Modelfile content.
        """
        # Default model parameters
        default_params = {
            "num_ctx": 4096,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.1
        }
        
        # Update with provided parameters
        if model_params:
            default_params.update(model_params)
        
        # Base standard model configuration
        modelfile_lines = [
            f"FROM {base_model}",
            f"# Modelfile for {model_name}",
            f"# Based on {base_model}",
            "",
            "# Model parameters",
        ]
        
        # Add model parameters
        for param, value in default_params.items():
            modelfile_lines.append(f"PARAMETER {param} {value}")
        
        modelfile_lines.append("")
        
        # Add system prompt if provided
        if system_prompt.strip():
            modelfile_lines.extend([
                "# System prompt from character",
                f"SYSTEM \"\"\"",
                system_prompt,
                "\"\"\"",
                "",
            ])
        
        # Add character context and template
        if manifest.strip():
            modelfile_lines.extend([
                "# Character context and conversation template",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "",
                "## Character Information",
                manifest,
                "",
                "## Conversation Rules",
                "- Always respond in character",
                "- Maintain consistent personality traits",
                "- Use appropriate language and tone",
                "- Remember previous interactions",
                "",
                "## Current Conversation",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        else:
            # Default template if no character context
            modelfile_lines.extend([
                "# Default conversation template",
                f"TEMPLATE \"\"\"",
                "{{ if .System }}{{ .System }}\\n\\n{{ end }}",
                "{{ .Prompt }}",
                "{{ .Response }}",
                "\"\"\"",
                "",
            ])
        
        return "\n".join(modelfile_lines)
    
    def generate_character_modelfile(self, model_name: str, base_model: str,
                                   character_data: Dict[str, Any]) -> str:
        """
        Generate Modelfile with full character integration.
        
        Args:
            model_name: Name of the model.
            base_model: Base model name or GGUF file path.
            character_data: Character data including system prompt and manifest.
            
        Returns:
            str: Generated Modelfile content.
        """
        # Extract character information
        system_prompt = character_data.get("system_prompt", "")
        manifest = character_data.get("manifest", "")
        model_params = character_data.get("model_params", {})
        
        # Check if base_model is a GGUF file
        if base_model.endswith('.gguf') or Path(base_model).exists():
            return self.generate_gguf_modelfile(
                model_name, base_model, system_prompt, manifest, model_params
            )
        else:
            return self.generate_standard_modelfile(
                model_name, base_model, system_prompt, manifest, model_params
            )
    
    def create_character_model_name(self, base_model: str, character_name: str) -> str:
        """
        Create a model name that combines base model and character name.
        
        Args:
            base_model: Base model name.
            character_name: Character name.
            
        Returns:
            str: Combined model name.
        """
        # Clean names for model naming
        import re
        
        # Remove hugginface URL prefixes
        clean_base = base_model.replace('hf.co/', '').replace('huggingface.co/', '')
        
        # Replace common separators with dashes
        clean_base = clean_base.replace(':', '-').replace('/', '-').replace('\\', '-').replace('_', '-')
        clean_character = character_name.replace(' ', '-').replace(':', '-').replace('/', '-').replace('\\', '-').replace('_', '-')
        
        # Remove any other non-allowed characters (keep only alphanumeric and dashes/dots)
        clean_base = re.sub(r'[^a-zA-Z0-9\-\.]', '', clean_base)
        clean_character = re.sub(r'[^a-zA-Z0-9\-\.]', '', clean_character)
        
        # Combine and ensure lowercase
        full_name = f"{clean_base}-{clean_character}".lower()
        
        # Remove repeated dashes and leading/trailing dashes/dots
        full_name = re.sub(r'-+', '-', full_name)
        full_name = full_name.strip('-.')
        
        return full_name
    
    def extract_character_from_modelfile(self, modelfile_content: str) -> Dict[str, Any]:
        """
        Extract character information from Modelfile content.
        
        Args:
            modelfile_content: Content of the Modelfile.
            
        Returns:
            Dict[str, Any]: Extracted character information.
        """
        character_data = {
            "system_prompt": "",
            "manifest": "",
            "model_params": {},
            "base_model": "",
            "model_type": "standard"
        }
        
        lines = modelfile_content.split('\n')
        current_section = None
        in_system = False
        in_template = False
        system_lines = []
        template_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check for FROM directive
            if line.startswith('FROM '):
                character_data["base_model"] = line[5:].strip()
                # Check if it's a GGUF file
                if character_data["base_model"].endswith('.gguf'):
                    character_data["model_type"] = "gguf"
            
            # Check for PARAMETER directives
            elif line.startswith('PARAMETER '):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    param_name = parts[1]
                    param_value = parts[2]
                    try:
                        # Try to convert to appropriate type
                        if '.' in param_value:
                            character_data["model_params"][param_name] = float(param_value)
                        else:
                            character_data["model_params"][param_name] = int(param_value)
                    except ValueError:
                        character_data["model_params"][param_name] = param_value
            
            # Handle SYSTEM section
            elif line == 'SYSTEM """':
                in_system = True
                current_section = "system"
            elif line == '"""' and in_system:
                in_system = False
                character_data["system_prompt"] = '\n'.join(system_lines)
                system_lines = []
            
            # Handle TEMPLATE section
            elif line == 'TEMPLATE """':
                in_template = True
                current_section = "template"
            elif line == '"""' and in_template:
                in_template = False
                # Extract manifest from template if present
                template_text = '\n'.join(template_lines)
                character_data["manifest"] = self._extract_manifest_from_template(template_text)
                template_lines = []
            
            # Collect content lines
            elif in_system:
                system_lines.append(line)
            elif in_template:
                template_lines.append(line)
        
        return character_data
    
    def _extract_manifest_from_template(self, template_content: str) -> str:
        """
        Extract manifest information from template content.
        
        Args:
            template_content: Content of the template.
            
        Returns:
            str: Extracted manifest information.
        """
        manifest_lines = []
        in_character_section = False
        in_rules_section = False
        
        for line in template_content.split('\n'):
            line = line.strip()
            
            # Look for character information section
            if "## Character Information" in line:
                in_character_section = True
                continue
            elif "## Conversation Rules" in line:
                in_character_section = False
                in_rules_section = True
                continue
            elif "## Current Conversation" in line:
                in_character_section = False
                in_rules_section = False
                break
            
            # Collect character information
            if in_character_section and line and not line.startswith('#'):
                manifest_lines.append(line)
        
        return '\n'.join(manifest_lines)
    
    def validate_modelfile(self, modelfile_content: str) -> Dict[str, Any]:
        """
        Validate Modelfile content and return validation results.
        
        Args:
            modelfile_content: Content of the Modelfile.
            
        Returns:
            Dict[str, Any]: Validation results.
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "model_type": "unknown",
            "has_system_prompt": False,
            "has_template": False,
            "base_model": ""
        }
        
        lines = modelfile_content.split('\n')
        
        # Check for required FROM directive
        has_from = any(line.strip().startswith('FROM ') for line in lines)
        if not has_from:
            validation_result["valid"] = False
            validation_result["errors"].append("Missing FROM directive")
        
        # Check for system prompt
        has_system = any('SYSTEM """' in line for line in lines)
        validation_result["has_system_prompt"] = has_system
        
        # Check for template
        has_template = any('TEMPLATE """' in line for line in lines)
        validation_result["has_template"] = has_template
        
        # Extract base model
        for line in lines:
            if line.strip().startswith('FROM '):
                base_model = line[5:].strip()
                validation_result["base_model"] = base_model
                if base_model.endswith('.gguf'):
                    validation_result["model_type"] = "gguf"
                else:
                    validation_result["model_type"] = "standard"
                break
        
        # Check for character context
        has_character_context = "Character Information" in modelfile_content
        if has_character_context:
            validation_result["warnings"].append("Character context detected in template")
        
        return validation_result