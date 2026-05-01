# Contingency Generator

Use this script to create offline personalised stage datasets (stages 1-4) and a teacher answer sheet.

## Command

From project root:

```bash
python contingency/generate_contingency.py --count 20
```

Optional flags:

- `--username-prefix` (default: `contingency`)
- `--output-dir` (default: `contingency/output`)
- `--run-name` (default: `contingency_<timestamp>`)

## Output

The script creates:

- `contingency/output/<run_name>/<username>/stage_1/instructions.md`
- `contingency/output/<run_name>/<username>/stage_1/stage1_dataset.csv`
- `contingency/output/<run_name>/<username>/stage_2/instructions.md`
- `contingency/output/<run_name>/<username>/stage_2/stage2_dataset.csv`
- `contingency/output/<run_name>/<username>/stage_3/instructions.md`
- `contingency/output/<run_name>/<username>/stage_3/stage3_signal_readings.csv`
- `contingency/output/<run_name>/<username>/stage_4/instructions.md`
- `contingency/output/<run_name>/<username>/stage_4/stage4_drone_fleet.zip`
- `contingency/output/<run_name>/teacher_answer_sheet.csv`

The answer sheet contains the correct personal 6-digit code for each stage and participant.
