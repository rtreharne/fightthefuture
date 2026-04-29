STAGE_COUNT = 5
FINAL_STAGE = STAGE_COUNT
COMPLETED_STAGE = STAGE_COUNT + 1

# Stage 1 is solo; stages 2-5 require exact collaboration sizes.
STAGE_GROUP_SIZES = {
    1: 1,
    2: 2,
    3: 4,
    4: 8,
    5: 8,
}

STAGE_DETAILS = {
    1: {
        "title": "Stage 1: Signal Capture",
        "instructions": "Placeholder challenge instructions for stage 1.",
    },
    2: {
        "title": "Stage 2: Pattern Decode",
        "instructions": "Placeholder challenge instructions for stage 2.",
    },
    3: {
        "title": "Stage 3: Protocol Recovery",
        "instructions": "Placeholder challenge instructions for stage 3.",
    },
    4: {
        "title": "Stage 4: Mesh Synchronisation",
        "instructions": "Placeholder challenge instructions for stage 4.",
    },
    5: {
        "title": "Stage 5: Final Relay",
        "instructions": "Placeholder challenge instructions for stage 5.",
    },
}
