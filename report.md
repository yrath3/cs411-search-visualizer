# Project 1 Report: Intelligent Search Visualizer

> [!IMPORTANT]
> **AUTOGRADER COMPLIANCE INSTRUCTIONS:**
> This report is parsed automatically by the autograder. To ensure you receive full credit for your work:
> 1. **Do not modify** the section headers (`## ...`) or bold field keys (e.g., `**Name:**`, `**Selected Region:**`, `**Live Deployment URL:**`, etc.).
> 2. **Write your answers directly after** the colon `:` of each field, replacing the placeholder text completely (including the outer brackets `[` and `]`).
> 3. **Maintain the file structure**. Changing headers, bold titles, or deleting lines can cause the autograder to miss your responses and award 0 marks.

---

## Student Information 
- **Name:** Yashraj Rathore
- **UID (netID):** yrath3
- **UIN:** 661286836

---

## Section 1: Selected City Region
- **Selected Region:** Illinois, USA

---

## Section 2: Map Graph Configuration
- **Total Cities Configured:** 28
- **Total Connection Edges:** 49
- **Graph Fully Connected:** Yes

---

## Section 3: Local Verification & Search Algorithms
*Check the algorithms you successfully ran and verified on your local development server by placing an `x` in the brackets (e.g., `[x]`):*
- [x] Breadth-First Search (BFS)
- [x] Depth-First Search (DFS)
- [x] Uniform Cost Search (UCS)
- [x] Iterative Deepening Search (IDS)
- [x] Greedy Best-First Search (Greedy)
- [x] A* Search (A*)

---

## Section 4: Deployed and Presentation Information
- **Deployment Platform:** Render
- **Live Deployment URL:** https://cs411-search-visualizer-sy26.onrender.com
- **Video Presentation Link:** [Provide an accessible link to your 5–7 minute video presentation]

---

## Section 5: Discussion
- **Which search algorithm is best for this route finding problem?** 
    I think A* is the best algorithm for this route finding problem. It found the lowest route at 404.94 miles, which was the same as UCS, but it only expanded 23 nodes compared to UCS expanding 28. A* works well because it uses the straight-line distance to the goal to help decide where to search next. Since the actual road distance cannot be shorter than the straight line distance, the heuristic does not overestimate. Greedy only expanded 9 nodes, but it gave a longer route of 418.70 miles, so A* gives a better balance between finding the best route and being efficient.
- **Search Efficiency (Nodes expanded/time taken comparison):** BFS got 404.94 miles with 25 nodes, DFS got 786.82 miles with 20 nodes, UCS got 404.94 miles with 28 nodes, IDS got 404.94 miles with 632 nodes, Greedy got 418.70 miles with 9 nodes, and A* got 404.94 miles with 23 nodes. IDS was clearly the least efficient in terms of nodes because it keeps starting over from depth 0 each time. DFS did not expand that many nodes, but the route it found was almost double the optimal distance. BFS and IDS both found a 7 road route, which happened to be the cheapest route here, even though they are not actually looking at mileage. UCS and A* both found the best route, but A* searched fewer nodes because the heuristic helped guide it. Since all of the algorithms took under 1 ms, I think comparing the number of nodes expanded gives a better idea of efficiency here.
- **Link the idea of search algorithm to today Generative AI.** 
    Search algorithms are also pretty similar to how Generative AI works today. An LLM is basically choosing between a huge number of possible next words or tokens every time it generates something. Beam search keeps a few of the best possible sentences going at once instead of checking every single option. The probability the model gives to different outputs is kind of like a heuristic because it helps decide which path looks the most promising. Things like chain of thought and tree of thought also have different reasoning paths, similar to BFS or DFS. AI agents do something similar by searching through different actions until they find a path that completes the task.

