#!/usr/bin/env python3
"""
Test script for Chat Memory System.

This script provides a simple way to test the ChatMemory functionality
without running the full chatbot application.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from chat_memory import ChatMemory


def test_chat_memory():
    """Test the ChatMemory functionality."""
    print("Testing ChatMemory...")
    
    # Create memory manager
    memory = ChatMemory(recent_limit=5, summary_trigger_limit=8)
    
    # Test basic functionality
    print("1. Testing basic message addition...")
    memory.add_message("user", "Hello, how are you?")
    memory.add_message("assistant", "I'm doing great, thank you!")
    memory.add_message("user", "What's the weather like today?")
    memory.add_message("assistant", "It's sunny and warm outside.")
    
    status = memory.get_status()
    print(f"   Status: {status}")
    assert status['recent_messages_count'] == 4
    assert status['summary_length'] == 0
    
    # Test memory usage percentage
    print("2. Testing memory usage tracking...")
    for i in range(4):
        memory.add_message("user", f"Message {i+5}")
    
    status = memory.get_status()
    print(f"   Status after 8 messages: {status}")
    assert status['recent_messages_count'] == 5  # Should keep only recent
    assert status['total_messages_processed'] == 8
    
    # Test summarization trigger
    print("3. Testing summarization trigger...")
    memory.add_message("user", "This should trigger summarization")
    
    status = memory.get_status()
    print(f"   Status after trigger: {status}")
    assert status['has_pending_summarization'] == True
    
    # Test summarization processing
    print("4. Testing summarization processing...")
    test_summary = "User asked about weather, assistant responded about sunny day."
    memory.process_summarization_result(test_summary)
    
    status = memory.get_status()
    print(f"   Status after processing: {status}")
    assert status['summary_length'] > 0
    assert status['summaries_created'] == 1
    assert status['has_pending_summarization'] == False
    
    # Test context generation
    print("5. Testing context generation...")
    context = memory.get_context_for_llm()
    print(f"   Generated context: {repr(context)}")
    assert "Previous summary:" in context
    assert "Recent conversation:" in context
    
    # Test clearing
    print("6. Testing memory clearing...")
    memory.clear()
    status = memory.get_status()
    print(f"   Status after clear: {status}")
    assert status['recent_messages_count'] == 0
    assert status['summary_length'] == 0
    assert status['total_messages_processed'] == 0
    assert status['summaries_created'] == 0
    
    return True


def test_summarization_prompt():
    """Test the summarization prompt generation."""
    print("\nTesting summarization prompt...")
    
    memory = ChatMemory()
    
    # Create test messages
    test_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm good, thanks!"},
    ]
    
    # Format for summarization
    formatted = memory._format_messages_for_summarization(test_messages)
    print(f"   Formatted messages: {repr(formatted)}")
    
    # Create prompt
    prompt = memory._create_summarization_prompt(formatted)
    print(f"   Summarization prompt: {repr(prompt)}")
    
    assert "user: Hello" in prompt
    assert "assistant: Hi there!" in prompt
    assert "Summarize the key points" in prompt
    
    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\nTesting edge cases...")
    
    # Test empty memory
    memory = ChatMemory()
    context = memory.get_context_for_llm()
    assert context == ""
    
    # Test single message
    memory.add_message("user", "Hello")
    context = memory.get_context_for_llm()
    assert "Recent conversation:" in context
    
    # Test summary cleaning
    long_summary = "A" * 1500 + "This is the end"
    cleaned = memory._clean_summary(long_summary)
    assert len(cleaned) <= 1000
    assert cleaned.endswith("...")
    
    return True


def main():
    """Run all tests."""
    print("Chat Memory System Test Suite")
    print("=" * 40)
    
    tests = [
        ("Basic Functionality", test_chat_memory),
        ("Summarization Prompt", test_summarization_prompt),
        ("Edge Cases", test_edge_cases)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   Test {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Chat Memory system is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    main()