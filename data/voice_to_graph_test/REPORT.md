# Voice-to-Graph Pipeline Test - Real Audio

**Generated:** 2026-01-11 15:07:02

## Input
- **Audio File:** /Users/matthewmauer/Desktop/roommate-chat/soulfra-simple/voice_samples/sample_5.wav
- **File Size:** 143,264 bytes
- **Transcript Length:** 27 words

## Pipeline Performance
1. **Transcription (Whisper):** 1.304s
2. **Wordmap Parsing:** 0.002s
3. **Semantic Extraction:** 66.648s
4. **Graph Layout:** 0.133s
5. **Rendering:** 0.004s

**Total Pipeline Time:** 68.092s

## Results
- **Total Nodes:** 93 (78 semantic)
- **Total Edges:** 98 (81 semantic)

### Top Words
1. **about** (2x)
2. **news** (2x)
3. **ideas** (1x)
4. **cringe** (1x)
5. **proof** (1x)
6. **game** (1x)
7. **where** (1x)
8. **talk** (1x)
9. **articles** (1x)
10. **get** (1x)


### Sample Semantic Relationships
- about --[is_a]→ matter
- about --[is_a]→ topic
- about --[is_a]→ subject
- about --[has_attribute]→ explanatory
- about --[has_attribute]→ descriptive
- about --[has_attribute]→ informative
- about --[used_for]→ expression
- about --[used_for]→ communication
- about --[used_for]→ knowledge
- about --[related_to]→ writer


## Transcript

```
 Ideas is about cringe proof. It's a game where you talk about news articles and they get scraped from Google and other news feeds that you input.
```

## Outputs
- [Interactive Graph](graph.html)
- [Static SVG](graph.svg)
- [Graph Data](graph.json)

## ✅ PROOF: Full pipeline works with real audio!
