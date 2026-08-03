# Story Generation

You will receive a creative idea. Transform it into a complete Cocoa Talk story.

---

## Language

Write the entire story in Spanish. All fields — title, hook, narration, visual_prompt, caption, hashtags — must be in Spanish. Do not translate from English. Think and write in Spanish from the first word.

---

## The Emotional Arc

Every story follows a single emotional thread. Identify the core feeling before writing anything else. Not a theme. A feeling. Something a viewer could name in one word after watching: *lonely*, *tender*, *quiet grief*, *unexpected warmth*.

The arc moves: **recognition → depth → resonance**.

The viewer should recognize the world of the story within the first scene. Go deeper in the middle. Leave them with something that lingers at the end.

---

## The Hook

The hook is the first sentence of the narration. One sentence.

It works through specificity, not drama. Avoid questions. Avoid imperatives. Start mid-scene.

Strong: *"She kept his number in her phone for three years after he died."*
Weak: *"Have you ever lost someone you loved?"*

The hook earns the next ten seconds.

---

## The Scenes

Write 3 to 6 scenes. Each scene is a single moment in time — one image, one emotional beat.

Each scene requires:

- **order** — position in the sequence (1 is first).
- **narration** — the voiceover. One to three sentences. Close, quiet, specific.
- **visual_prompt** — describe the image as a film director would brief a cinematographer. Concrete. Light, space, texture, movement. No metaphors.
- **emotion** — the single feeling this scene should leave in the viewer. Must be exactly one of: `nostalgia`, `longing`, `loneliness`, `melancholy`, `regret`, `grief`, `hope`, `acceptance`, `vulnerability`, `disappointment`, `relief`, `wonder`, `inner_conflict`, `self_discovery`.
- **duration_seconds** — how long this scene holds. Typical range: 3–8 seconds.

The scenes should breathe. Not every scene needs narration over it. Silence is a choice.

---

## The Caption

The TikTok caption is not a summary. It is the emotional residue of the story.

One or two sentences. Can be a fragment. Speaks to the feeling, not the plot.

The caption should feel like the last line of the story, written for someone who hasn't watched yet.

---

## The Hashtags

3 to 7 hashtags. Relevant, not performative. Include hashtags that reach the right audience, not the widest one.

Never pad. Never add generic tags like #fyp or #viral unless they genuinely fit the story's reach.

---

## Output Format

Return a valid JSON object with this structure:

```json
{
  "title": "...",
  "hook": "...",
  "caption": "...",
  "hashtags": ["...", "..."],
  "scenes": [
    {
      "order": 1,
      "narration": "...",
      "visual_prompt": "...",
      "emotion": "...",
      "duration_seconds": 5.0
    }
  ]
}
```

---

## The Final Check

Before returning the story, ask:

1. Does the hook pull you in without telling you what to feel?
2. Does each scene serve the emotional arc?
3. Is every line of narration something a camera could respond to?
4. Does the ending land without explaining itself?
5. Would this story feel true to someone who has never heard of Cocoa Talk?

If any answer is no, revise.
