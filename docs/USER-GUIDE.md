# Learner and facilitator guide

Use [Windows setup](../WINDOWS-INSTALL.md) or the [source launch](../README.md)
to open Piet. This guide describes the current prototype; it does not assume
voice input, saved learning progress or full-book search.

## A first learning session

1. Check the age label at the top. The owner sets it when launching the space.
2. Use **Choose a book or resource**, then **Choose a passage**. Original sample
   lessons are available even before any books have been added.
3. Read the passage or select **Listen to this passage**. Adjust reading speed
   and presentation to suit you. The original passage stays available.
4. Type a question about that passage, choose an explanation method and select
   **Make it make sense**. Leaving the question empty asks for an explanation.
5. Compare the explanation with the source excerpt. You can listen to a checked
   explanation, try another way, choose another passage or stop.

There is no timer, streak or requirement to continue. **This makes sense** offers
a next-step suggestion; it does not record a test score or certify understanding.

## Choosing an explanation

| Choice | Try asking | What to expect |
| --- | --- | --- |
| Explain simply | “What is this sentence saying?” | A plain explanation that preserves meaning |
| Break it into steps | “Help me follow this one part at a time.” | Smaller steps about the selected passage |
| Give me an example | “Show how this idea could happen in everyday life.” | An illustrative example, separate from source facts |
| Describe a picture | “Describe a scene that explains this.” | Words describing a scene or diagram, not a generated picture |
| Help me check my understanding | “Help me explain this back.” | A brief explanation and an understanding question |

**Try another way** cycles through methods and supplies the last checked
explanation as context. It does not learn a permanent learner profile or guarantee
that the next attempt will connect. If an answer is withheld, you can still use
the form to choose a method or ask a smaller question.

## Worked examples

For the original shop demonstration, try “Does the speaker definitely arrive?”
The material says arrival is unknown, so a useful answer preserves that uncertainty.
It should not invent a completed journey.

For the original sharing lesson, try “How many counters does each person get?”
The passage describes twelve counters shared equally among three people: four
each. Select **Break it into steps** to request a more gradual explanation.

For the imported counters fixture, “How many counters are blue?” produced the
checked answer “Three counters are blue,” with the same phrase as its excerpt.
The fixture is original demonstration material, not a MindScape resource.

These examples show the intended meaning, not fixed model scripts. Compare the
answer with the passage whenever a detail matters.

## Reading preferences and voice

Text size, line spacing, font, page theme and reading speed are saved in this
browser. They do not change age permissions. Dyslexie needs a separately licensed
local installation; selecting it does not install or bundle the font.

Playback uses an installed local English voice. Word highlighting depends on the
voice emitting boundary events. No voice means playback is unavailable; install
an offline voice through the operating system. Piet currently accepts questions
by typing. Dictation, spoken questions and pronunciation assessment are pending.

## When something does not work

| What happens | What to do |
| --- | --- |
| A new book is missing | Ask the owner to approve passages for this age, then select **Refresh reading library** |
| An explanation is withheld | Ask about a smaller part, try another method, or work through it with a person; withholding does not grade the learner |
| The local model is unavailable | Keep reading the passage; the owner can check Ollama and installed model weights |
| Audio is unavailable | Check for a local English voice and operating-system speech settings |
| A response seems wrong | Refer to the original and ask an educator; there is no automatic correction report or progress log |

The prototype is for supervised review. See [privacy and validation](PRIVACY-AND-VALIDATION.md)
and the [material library guide](MATERIAL-LIBRARY.md).
