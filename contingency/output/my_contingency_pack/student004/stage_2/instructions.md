# Stage 2: Ghost Audit

## Narrative

AUGUR noticed the first breach.

Your personal terminal is still online, but the city systems are starting to fragment. Power, traffic, water and emergency services are all reporting maintenance activity. At first glance, the audit file looks routine.

It is not routine.

AUGUR has filled the city ledger with ghost operations: fake repairs, duplicated tasks and low-priority distractions designed to bury the real failures. Somewhere in this file is the next 6-digit access code, generated specifically for your operator identity.

This time, there is no broken starter script to repair. You need to write the logic yourself.

Filter the ledger. Find the real emergency records. Calculate the recovery load. Generate the code.

## Instructions

1. Create a new directory called stage_2 in your VS Code project.
2. Download the Stage 2 dataset from this page and save it in stage_2 as stage2_dataset.csv.
3. Create a new script file called stage2_ghost_audit.py inside your stage_2 directory.
4. Your script should read stage2_dataset.csv.
5. Keep only rows where status is ACTIVE, authentic is 1, and priority is greater than or equal to 4.
6. For each remaining row, calculate load = units * multiplier.
7. Add all load values together.
8. Add the value of bias_key.
9. Take the final total <a href="https://en.wikipedia.org/wiki/Modulo" target="_blank" rel="noopener noreferrer">modulo</a> 1000000.
10. Print the result as a 6-digit code, including leading zeroes if needed.
11. Follow the collaboration requirement shown on this page when submitting your code to AUGUR PODIUM.
