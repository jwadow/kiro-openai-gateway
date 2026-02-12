# -*- coding: utf-8 -*-

"""Unit tests for payload-level guard module."""

import json

from kiro.payload_guards import PayloadGuardConfig, apply_payload_guards


class TestPayloadGuards:
    """Tests for apply_payload_guards behavior."""

    def test_strips_empty_tool_uses_arrays(self):
        """
        What it does: Removes empty assistant toolUses arrays.
        Purpose: Kiro can reject explicit empty toolUses fields.
        """
        print("Setup: payload with empty toolUses array in history...")
        payload = {
            "conversationState": {
                "chatTriggerType": "MANUAL",
                "conversationId": "c1",
                "history": [
                    {
                        "assistantResponseMessage": {
                            "content": "assistant",
                            "toolUses": [],
                        }
                    }
                ],
                "currentMessage": {
                    "userInputMessage": {
                        "content": "hello",
                        "modelId": "claude-opus-4.6",
                        "origin": "AI_EDITOR",
                    }
                },
            }
        }

        print("Action: apply payload guards...")
        stats = apply_payload_guards(
            payload,
            PayloadGuardConfig(max_payload_bytes=1_000_000, max_history_entries=0),
        )

        print("Verify: empty toolUses removed and stats updated")
        history = payload["conversationState"]["history"]
        assert "toolUses" not in history[0]["assistantResponseMessage"]
        assert stats.stripped_empty_tool_uses == 1

    def test_trims_history_when_payload_exceeds_byte_limit(self):
        """
        What it does: Trims oldest history entries by byte budget.
        Purpose: Keep payload under configurable upstream-safe size.
        """
        print("Setup: oversized payload with long history entries...")
        long_text = "X" * 2000
        history = []
        for i in range(8):
            history.append(
                {
                    "userInputMessage": {
                        "content": f"user-{i} {long_text}",
                        "modelId": "claude-opus-4.6",
                        "origin": "AI_EDITOR",
                    }
                }
            )
            history.append({"assistantResponseMessage": {"content": f"assistant-{i}"}})

        payload = {
            "conversationState": {
                "chatTriggerType": "MANUAL",
                "conversationId": "c2",
                "history": history,
                "currentMessage": {
                    "userInputMessage": {
                        "content": "current",
                        "modelId": "claude-opus-4.6",
                        "origin": "AI_EDITOR",
                    }
                },
            }
        }

        print("Action: apply payload guards with tight byte limit...")
        stats = apply_payload_guards(
            payload,
            PayloadGuardConfig(max_payload_bytes=12_000, max_history_entries=0),
        )

        print("Verify: payload now under limit and history reduced")
        final_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        trimmed_history = payload["conversationState"].get("history", [])
        assert final_bytes <= 12_000
        assert len(trimmed_history) < len(history)
        if trimmed_history:
            assert "userInputMessage" in trimmed_history[0]
        assert stats.final_payload_bytes <= 12_000

    def test_repairs_orphaned_tool_results_after_trimming_or_malformed_flow(self):
        """
        What it does: Removes orphaned toolResults and preserves text in content.
        Purpose: Prevent generic 400 from invalid tool_use/tool_result pairing.
        """
        print("Setup: payload with orphaned history and current toolResults...")
        payload = {
            "conversationState": {
                "chatTriggerType": "MANUAL",
                "conversationId": "c3",
                "history": [
                    {
                        "userInputMessage": {
                            "content": "history user",
                            "modelId": "claude-opus-4.6",
                            "origin": "AI_EDITOR",
                            "userInputMessageContext": {
                                "toolResults": [
                                    {
                                        "toolUseId": "missing-history-id",
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": "history orphan output",
                                            }
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                    {"assistantResponseMessage": {"content": "assistant tail"}},
                ],
                "currentMessage": {
                    "userInputMessage": {
                        "content": "current user",
                        "modelId": "claude-opus-4.6",
                        "origin": "AI_EDITOR",
                        "userInputMessageContext": {
                            "toolResults": [
                                {
                                    "toolUseId": "missing-current-id",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": "current orphan output",
                                        }
                                    ],
                                }
                            ]
                        },
                    }
                },
            }
        }

        print("Action: apply payload guards...")
        stats = apply_payload_guards(
            payload,
            PayloadGuardConfig(max_payload_bytes=1_000_000, max_history_entries=0),
        )

        print("Verify: orphaned structured results removed, text preserved")
        history_user = payload["conversationState"]["history"][0]["userInputMessage"]
        history_ctx = history_user.get("userInputMessageContext", {})
        assert "toolResults" not in history_ctx
        assert "[Orphaned tool result]" in history_user.get("content", "")
        assert "history orphan output" in history_user.get("content", "")

        current_user = payload["conversationState"]["currentMessage"][
            "userInputMessage"
        ]
        current_ctx = current_user.get("userInputMessageContext", {})
        assert "toolResults" not in current_ctx
        assert "[Orphaned tool result]" in current_user.get("content", "")
        assert "current orphan output" in current_user.get("content", "")

        assert stats.removed_orphaned_history_tool_results == 1
        assert stats.removed_orphaned_current_tool_results == 1
