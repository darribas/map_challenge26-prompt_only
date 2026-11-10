
## Wednesday 4 November


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-1">#1</a> · Wed 4 Nov, 11:22</div><div class="note-text">ok have a read at SPEC.md for context and we can start working. When you&#x27;re ready, let&#x27;s get cracking...</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-2">#2</a> · Wed 4 Nov, 11:45</div><div class="note-text">all four nations and queen contiguity. Build the graphs first and don&#x27;t move beyond there for now</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-3">#3</a> · Wed 4 Nov, 11:54</div><div class="note-text">record this in LOG.md</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-4">#4</a> · Wed 4 Nov, 12:05</div><div class="note-text">drop the islands now from both the graph and the embeddings table. Make it a clear note of this step in the section before moving on</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-5">#5</a> · Wed 4 Nov, 12:05 · typed while Claude was working</div><div class="note-text">make a quick note to the log too</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-6">#6</a> · Wed 4 Nov, 12:07</div><div class="note-text">can you make a quick figure for me to inspect here (is it possible?) to see where the 12 issolates are?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-7">#7</a> · Wed 4 Nov, 12:09</div><div class="note-text">Yes, please add it on that section so there&#x27;s a record of it.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-8">#8</a> · Wed 4 Nov, 12:11 · typed while Claude was working</div><div class="note-text">Make this very lightweight, anything you need for a bass map used contextilly</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-9">#9</a> · Wed 4 Nov, 12:20</div><div class="note-text">ok, next is building similarity. There&#x27;s many distances that can work here, what do you recommend?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-10">#10</a> · Wed 4 Nov, 12:20</div><div class="note-text">cosine perhaps?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-11">#11</a> · Wed 4 Nov, 12:21</div><div class="note-text">let&#x27;s stick to cosine here. Open up a new section and let&#x27;s calculate the cosine distance (sklearn?) between every polygon and all of its queen neighors. Use the Graph we&#x27;ve created for this. Also, I think there&#x27;s scope here to make it work in parallel and it&#x27;d be significantly faster, what do you think? don&#x27;t do anything until we&#x27;re clear on what</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-12">#12</a> · Wed 4 Nov, 12:23</div><div class="note-text">Do you really not think it makes sense to do these in a few batches that are separated in parallel?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-13">#13</a> · Wed 4 Nov, 12:24</div><div class="note-text">What I&#x27;m thinking is split all of the polygons in 16 chunks, one per core in this machine, and then calculate the distances for those polygons and their neighbors in a separate worker and collect all the results afterwards.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-14">#14</a> · Wed 4 Nov, 12:26</div><div class="note-text">Is the code much more complex for the chunks?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-15">#15</a> · Wed 4 Nov, 12:27</div><div class="note-text">Go ahead with the parallel implementation then. Yes, split on the focal codes, I think.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-16">#16</a> · Wed 4 Nov, 12:32</div><div class="note-text">yes made an entry on the log.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-17">#17</a> · Wed 4 Nov, 12:37</div><div class="note-text">Okay, now I would like to create a simple table where every L SOA is a row and then there is a column for the nearest no, the most distant or dissimilar area. Let&#x27;s start with that. We will then think about the most dissimilar group of areas.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-18">#18</a> · Wed 4 Nov, 13:23</div><div class="note-text">ok now let&#x27;s think about how a distance between the focal area and its neighbors would work. Two thoughts: 1) we get the distances between i and every j in the neighborhood, and then average it; 2) we average the embedding of the neighbors and then the distance. Thoughts?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-19">#19</a> · Wed 4 Nov, 13:46</div><div class="note-text">ok let&#x27;s calculate both for now, let&#x27;s think how we&#x27;d compute them</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-20">#20</a> · Wed 4 Nov, 13:52</div><div class="note-text">Yeah, let&#x27;s go ahead.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-21">#21</a> · Wed 4 Nov, 14:00</div><div class="note-text">Show me here the scatter plot please.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-22">#22</a> · Wed 4 Nov, 14:23</div><div class="note-text">Okay, I think we have all the pieces to start exploring a few maps. Let&#x27;s pick the focal area with the highest distance of either type and make me a few simple maps. Use a satellite imagery baseline and include the focal area and all of its neighbors, making sure that you can see the boundary line of the LSOA and the satellite background. Start by building those on your scratch pad and show me the images here.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-23">#23</a> · Wed 4 Nov, 14:31</div><div class="note-text">Okay, this is a great first start. Let&#x27;s iterate a little bit in how I want the figure to look like and then once we have a template we&#x27;ll create it for a few more cases. I really like option one, but maybe instead of white lines you can pick another color, maybe red, or use red for the focal and yellow for the rest. And I would also want to have on a corner a very simplified map of the UK in either dark grey or light grey with an accent color for the location where these L SOAs are. So it&#x27;s easier to place on the general map.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-24">#24</a> · Wed 4 Nov, 14:52</div><div class="note-text">It is a lot. I think it&#x27;s almost ready. One more thing I would like to try. Can we maybe fade the base map in the areas that are not part of the vocal or neighbors. What I&#x27;m thinking is that you could maybe get a polygon that covers everything that is not part of a polygon in the image and then apply a light Dark transparency to fade it away.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-25">#25</a> · Wed 4 Nov, 14:56</div><div class="note-text">Fantastic. Let&#x27;s iterate a couple on of items more. One, show me a few alternatives with different colors for the fade. I like your idea of a light one that makes it more washed, but think also of at least two more to compare. Then I also want you to think of other combinations of the lines that highlight the L SOAs. Red and yellow are very effective but are not, at least in these tonalities, the most aesthetic. Show me at least five combinations. And then finally, the inset, given that we have the fade, let&#x27;s do one without any rectangle. I just want the shape of the UK and pick the color for the UK then based on a contrast with whatever the fade is. Take these three dimensions and make me a grid of combinations to see which one Ilike best.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-26">#26</a> · Wed 4 Nov, 16:26</div><div class="note-text">actually, can you try one more using the Imaco color palette? If you don&#x27;t know what that is, get a sense from imago.ac.uk</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-27">#27</a> · Wed 4 Nov, 16:49</div><div class="note-text">Let’s stick with C1 for now. Add it as the template and update for the notebook and the log</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-28">#28</a> · Wed 4 Nov, 17:45</div><div class="note-text">Actually I want the UK polygon and all the text in the image to be imago grey. See the actual palette attached and update accordingly</div><img src="conversation/img/019.jpg" alt="Image attached to prompt 28" loading="lazy"></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-29">#29</a> · Wed 4 Nov, 21:47</div><div class="note-text">I like with the official colors a bit more. A couple of further iterations: 1) if you’re using Imago grey (#4a4a49), can you make the text in bold? Also, can you use the official font, which is figtree? 2) Make the UK polygon in Imago grey also, and the dot on that polygon in the orange of the focal area. I really like the setup of the image, it looks like a Polaroid picture, can we keep/reinforce that for when we export?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-30">#30</a> · Wed 4 Nov, 21:53 · typed while Claude was working</div><div class="note-text">Ok almost perfect: one more thing on the Polaroid side: can you keep a larger margin at the bottom than at the top (that’s how Polaroids are no?) and also can you make it somehow so that it keeps this layout clear even if it’s displayed against white? Maybe with a thin border line?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-31">#31</a> · Wed 4 Nov, 21:58</div><div class="note-text">Let’s start with the top 5 for each measure</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-32">#32</a> · Wed 4 Nov, 22:06</div><div class="note-text">OK I see the point of these, they’re true but not the most interesting. Maybe let’s switch gears from neighboring sets to pairs. Let’s look at the largest distance between a pair of neighbors. Before that, include these top five in the notebook and log if not there yet, and start a new section for this.</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-33">#33</a> · Wed 4 Nov, 22:09</div><div class="note-text">Yes, let’s expand the Polaroid approach to also be able to accommodate pairs</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-34">#34</a> · Wed 4 Nov, 22:19</div><div class="note-text">OK two ideas to try to find more interesting “Polaroids”:<br><br>1. Restrict the search within the bounds of specific cities (e.g., London, Liverpool). That way, the chances of countryside vs urban are lower<br><br>2. Try a different approach:<br>	a. Cluster all the LSOAs in a bunch of similar groups with say K-means (e.g., k=100)<br>	b. Explore if those clusters capture features or items (e.g., industrial, residential, agriculture, different mixes)<br>	c. Then set up the search for different neighborhoods at the cluster level (e.g., what is the industrial estate next the most different landscape?)<br><br>what do you think?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-35">#35</a> · Wed 4 Nov, 22:22</div><div class="note-text">I said 100 randomly, do you think a different number might be best to start with?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-36">#36</a> · Wed 4 Nov, 22:23</div><div class="note-text">OK log this exploration and lets move its development to a second notebook. To make sure we rely on the same tooling, is the Polaroid template, etc. In a separate .py file that can be used across notebooks? If not, make it so</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-37">#37</a> · Wed 4 Nov, 22:31</div><div class="note-text">20 and 100</div></div>
```


## Thursday 5 November


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-38">#38</a> · Thu 5 Nov, 22:11</div><div class="note-text">Show me the contact card for urban centers in the k20</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-39">#39</a> · Thu 5 Nov, 22:12</div><div class="note-text">Can you find a better fit for that description in k100?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-40">#40</a> · Thu 5 Nov, 22:17</div><div class="note-text">Let’s stick with 95. Let’s play with the Polaroid, can you show me the Polaroid of the top 5 distances in cluster 95?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-41">#41</a> · Thu 5 Nov, 22:21</div><div class="note-text">I’d like to get a sense of how big those distances are. Add a flag to the Polaroid method that when True, adds a dense histogram of all distances in the entire dataset, not the cluster, and a vertical line on the value of the distance of the pair represented in the Polaroid. Make look nice, elegant, and in line with the aesthetic of the current figure. Show me that to 5 again then</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-42">#42</a> · Thu 5 Nov, 22:26</div><div class="note-text">How are the Glasgow ones different? They seem similar to me</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-43">#43</a> · Thu 5 Nov, 22:29</div><div class="note-text">OK let’s explore Polaroids in this cluster but for the lag rather than pairs. Show me the top 5</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-44">#44</a> · Thu 5 Nov, 22:35</div><div class="note-text">One more tweak to the Polaroid: do you think we can fit an additional graph that is a horizontal bar chart with one bar per embedding dimension and two bars/values in each bar, one orange and one green, corresponding to the values for each area respectively. Basically, I want to visualise the differences in the two embeddings being compared. Maybe this is too crammed and is instead better to do it in lieu of the histogram? Add a flag on the Polaroid method and show me a couple of examples</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-45">#45</a> · Thu 5 Nov, 22:39</div><div class="note-text">Let’s try the difference and also this other option: one bar only with both orange and green on top of each other with transparency. That way similar dimensions are obvious and don’t take up space, while different ones are also clear</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-46">#46</a> · Thu 5 Nov, 22:43</div><div class="note-text">Yeah give it a try</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-47">#47</a> · Thu 5 Nov, 22:47</div><div class="note-text">Do that and update the log and notebook with this exploration</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-48">#48</a> · Thu 5 Nov, 23:52</div><div class="note-text">Scan the 100 clusters and provide me a list of pending other clearly delimited entities such as docks, parks, golf courses, industrial estates, etc.</div></div>
```


## Monday 9 November


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-49">#49</a> · Mon 9 Nov, 23:15</div><div class="note-text">for each of the entitites, show me the top 3 polaroids</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-50">#50</a> · Mon 9 Nov, 23:24</div><div class="note-text">OK I need to be wrapping this up. I&#x27;d like the submission to the map challenge to be a couple of polaroids that are striking, highlight well the value of embeddings, and are a good example of the point they&#x27;re traying to make. Which specific ones would you pick of all we&#x27;ve created?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-51">#51</a> · Mon 9 Nov, 23:27</div><div class="note-text">Show me the images again with the names</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-52">#52</a> · Mon 9 Nov, 23:30</div><div class="note-text">I’d replace the third one with another one that is entirely within a human settlement. What do you propose?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-53">#53</a> · Mon 9 Nov, 23:32</div><div class="note-text">Ohhh why is the middle in the bottom row there? Both seem similar?</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-54">#54</a> · Mon 9 Nov, 23:35</div><div class="note-text">Yes</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-55">#55</a> · Mon 9 Nov, 23:50</div><div class="note-text">Ok log up to here and update notebooks as required</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-56">#56</a> · Mon 9 Nov, 23:55 · typed while Claude was working</div><div class="note-text">Ok I want to refine the final submissions. I like the cases, but I want to tweak the Polaroid template. Perhaps both the density plot and the embedding graph are too nerdy. Let’s get rid of them and, instead, write a haiku that brings the most interesting aspect of the pair (given the discussion we’ve had here).<br><br>Also, separate, here’s an idea: what if we only include the reservoir as the most different, and then find the most similar pair? Include also, for good measure, the most similar urban pair</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-57">#57</a> · Mon 9 Nov, 23:56 · typed while Claude was working</div><div class="note-text">Use a typewriter font for the haiku, it’ll give more of a Polaroid vibe</div></div>
```


## Tuesday 10 November


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-58">#58</a> · Tue 10 Nov, 00:04</div><div class="note-text">I like the reservoir and the two very similar ones, let’s keep those. <br><br>Open up a new final notebook that all it does is the process from start to end to create the final submission, detached from all the analysis it brought us here</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-59">#59</a> · Tue 10 Nov, 00:08</div><div class="note-text">Log up to here and remove leftovers. <br><br>This viajen is promoting only, you check/confirm the names please</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-60">#60</a> · Tue 10 Nov, 00:14</div><div class="note-text">OK great, now we need the text for the post on LinkedIn. Make one that is succinct, gets the point across, and is not very Claudian or LinkedIn’y</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-61">#61</a> · Tue 10 Nov, 00:16</div><div class="note-text">OK great, commit this text to the submission notebook</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-62">#62</a> · Tue 10 Nov, 00:16</div><div class="note-text">Update the log too</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-63">#63</a> · Tue 10 Nov, 00:23</div><div class="note-text">Great now the final move. I’d like to turn all this material in a simple website (quarto?) that lets the user see first and foremost the context and submission, and then dig into the backstory of how we got there. Keep in mind the Polaroid theme for the styling of the site. And, very important, find a way of exploring this full conversation we’ve had and include it there, once as a full transcript but also if you find cool ways to thread it through the rest of the site. Once you’re done here, I’ll take this whole folder and dump it on a github repo where I can turn Pages on as you tell me. Make it all simple and easy to run afterwards on my own (so good documentation). Ahhh, and I’ll not include the data files in the repo, so sound for that</div></div>
```


```{=html}
<div class="note prompt"><div class="note-meta"><a href="transcript.html#p-64">#64</a> · Tue 10 Nov, 09:58</div><div class="note-text">ok I created a new GH repo at https://github.com/darribas/map_challenge26-prompt_only.git Use your gh credentials to check the work here there</div></div>
```
