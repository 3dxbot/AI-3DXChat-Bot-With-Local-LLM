import os
import json
import sys

# Mocking config and CharacterProfile for testing logic
class CharacterProfile:
    def __init__(self, name="New Character", greeting="", global_prompt="", manifest="", memory_cards=None):
        self.name = name
        self.greeting = greeting
        self.global_prompt = global_prompt
        self.manifest = manifest
        self.memory_cards = memory_cards if memory_cards else []

    def to_dict(self):
        return {
            "name": self.name,
            "greeting": self.greeting,
            "global_prompt": self.global_prompt,
            "manifest": self.manifest,
            "memory_cards": self.memory_cards
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", "New Character"),
            greeting=data.get("greeting", ""),
            global_prompt=data.get("global_prompt", ""),
            manifest=data.get("manifest", ""),
            memory_cards=data.get("memory_cards", [])
        )

def test_serialization():
    char = CharacterProfile(
        name="TestBot", 
        greeting="Hello!", 
        global_prompt="Be helpful", 
        manifest="AI Assistant",
        memory_cards=[{"key": "user", "data": "John"}]
    )
    
    data = char.to_dict()
    assert data["name"] == "TestBot"
    assert len(data["memory_cards"]) == 1
    assert data["memory_cards"][0]["key"] == "user"
    
    new_char = CharacterProfile.from_dict(data)
    assert new_char.name == "TestBot"
    assert new_char.greeting == "Hello!"
    assert len(new_char.memory_cards) == 1
    
    print("Serialization test passed!")

if __name__ == "__main__":
    test_serialization()
