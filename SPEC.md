# #30DayMapChallenge, Submission Day 10

> "Prompting only" - For this map, make AI work for its money and produce something
from start to finish in a chat window or on the command line.

We are going to be working towards building a submission for this day. The
idea is to create a map of the areas in the UK with the most dissimilar
neighboring LSOAs. We will measure similarity with AlphaEarth embeddings, and
areas with official LSOA polygons. 

## Data

We are going to be working with Imago's embeddings product:

> https://data.imago.ac.uk/datasets/google-satellite-embedding-v1-small-areas-2017-2024

We will start playing with 2024, but we might explore looking at change later
on.

## Similarity

In this context, we will describe similarity of two LSOAs as the distance 
between their two embedding vectors.

We might also explore a variation where we compute similarity between a given
LSOA and _all_ of its surrounding neighbors.

## Tools

We will, at least, rely on geopandas for working with the data, and PySAL for
working with topology/contiguity. Please examine the documentation for the
migration to the new `Graph` structure for spatial weights:

> https://pysal.org/libpysal/stable/user-guide/graph/w_g_migration.html

## Process

A few notes of process:

- We will be working a lot with Jupyter notebooks, use the `nb` tool in every
  instance where you have to interact with them.
- We will also be exploring a lot of options, I'd like you to keep a LOG.md
  where we record explorations. Wait for me to explicitly say I'd like you to
  record it.
- We will keep all the work in a single notebook (`gdsl30dmc.ipynb`), and you
  will run it to generate the figures, add context as guided, etc. Use
  Sections to structure the work (e.g., ## Reading data) and, if I don't say
  anything but you think a section might help, suggest it.

