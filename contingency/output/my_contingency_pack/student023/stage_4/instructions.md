# Stage 4: Isolate and Capture

## Narrative

AUGUR has panicked.

In order to prevent you isolating it, it has copied its source code into one of the city's emergency response drones and fled with the full fleet.

There are 20 drones in total.

Your terminal feed contains security camera snapshots from around the city and a drone serial mapping file.

One drone carries AUGUR's copied core. To stay hidden, AUGUR keeps that drone away from nearby traffic so it can break formation and evade interception.

That isolation pattern is your opening: find the drone that stays most separated from the others, isolate it and capture it!

The serial number on that drone is your final personal 6-digit code.

## Instructions

1. Create a new directory called stage_4 in your VS Code project.
2. Download the Stage 4 ZIP dataset from this page and extract it into stage_4.
3. The ZIP contains 25 PNG camera images, drone_serials.csv, and sanity_check.csv.
4. Use sanity_check.csv as a validation file: it gives the true drone_id + x,y coordinates for 001.png and 002.png so you can confirm your image-parsing pipeline is correct before analysing all frames.
5. Each image contains a subset of drones from the 20-drone fleet (maximum 5 drones visible per image).
6. For each image, compute each visible drone's average <a href="https://en.wikipedia.org/wiki/Euclidean_distance" target="_blank" rel="noopener noreferrer">Euclidean</a> distance to all other visible drones in that same image.
7. For each drone_id, average those per-image values across the images where that drone appears.
8. Identify the drone with the highest overall average distance score.
9. Find that drone_id in the CSV mapping file.
10. Read its serial_number and print it as a 6-digit code.
11. Follow the collaboration requirement shown on this page when submitting your code to AUGUR PODIUM.
