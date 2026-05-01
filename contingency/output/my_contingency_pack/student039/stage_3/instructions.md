# Stage 3: Signal Test

## Narrative

AUGUR has stopped simply hiding information.

It is now producing false signals.

Across the city, district signal monitors are reporting strange behaviour. Some variation is expected: sensors drift, networks lag, and old infrastructure makes noises that nobody fully understands. But one district is not behaving normally.

Your personal terminal has captured signal readings from multiple city districts. Most of the data is ordinary background noise. One district contains a pattern that should not be there.

Do not trust a single reading. Do not trust a quick glance. AUGUR is counting on you mistaking noise for evidence.

Compare the districts. Find where the `signal_strength` pattern breaks. Then recover the district code and submit it to AUGUR PODIUM.

You remember one of your old lecturers talking about ANOVA for this kind of problem. He did say "It'll come in handy one day!". And damnit, he was right.

## Instructions

1. Create a new directory called stage_3 in your VS Code project.
2. Download the Stage 3 dataset from this page and save it in stage_3 as stage3_signal_readings.csv.
3. Create a new script file in your preferred programming language inside your stage_3 directory.
4. Your script should read stage3_signal_readings.csv.
5. The dataset contains signal readings from several city districts.
6. Use ANOVA and post-hoc tests on signal_strength across districts.
7. Find the abnormal district where signal_strength behaves differently from the others.
8. Once you identify the abnormal district, read its district_code value.
9. Print that district_code as a 6-digit code, including leading zeroes if needed.
10. Enter that 6-digit code into AUGUR PODIUM.
11. HINT: Mention ANOVA and post-hoc tests explicitly in your chat prompts.
12. Follow the collaboration requirement shown on this page when submitting your code to AUGUR PODIUM.
