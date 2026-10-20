---
cursor:
  subagentId: "bc-748824e2-d72b-5dea-9a67-502b42ae5c5b"
---

# W2 exam-scope test results

Ran the filed 106-question set against latest GitHub `main` on this Mac. Separate clone (`/tmp/ChatbotChallenge2026Team16-examtest`). Did **not** commit or push `.env`. Did not print the key.

Question set:

- `internal/exam_scope_questions.json`
- `internal/exam_scope_questions.md`
- `docs/w2-exam-scope-test-questions.md`

## Return summary

| Item | Value |
|---|---|
| GitHub `main` SHA | `aad6dc9e816d3186ce456d198c16d19a5deb0290` |
| Matches `origin/main` | yes |
| Key found | **yes** (`~/ChatbotChallenge2026Team16/submission_repo/.env`, copied into the test clone only) |
| Questions run | **106 / 106** (G01–G16 all; X01–X90 all) |
| Results path | `docs/w2-exam-scope-test-results.md` |
| Given | pass 5 · partial 2 · fail 9  (16 run) |
| Extra | pass 23 · partial 5 · fail 62  (90 run) |
| Total | pass 28 · partial 7 · fail 71  (106 run) |

Pass = gold facts present (spelling variants OK: modelling/modeling; 工学院 = Faculty of Engineering; 增材制造 = additive manufacturing). Partial = some required facts only (e.g. PVC but not polycarbonate). Fail = wrong, unknown, or missing the gold.

## Setup

1. Found key in `~/ChatbotChallenge2026Team16/submission_repo/.env` (names only: `AZURE_OPENAI_KEY` and the usual gateway vars). Copied to the `/tmp` clone. `.env` is gitignored; never staged.
2. `python3 -m venv` + `pip install -r requirements.txt` already present from the earlier attempt.
3. Stock `check_setup.py` on this SHA calls `chat(..., max_tokens=5)` but `bot.llm.chat` takes `max_completion_tokens` → TypeError. Local one-line patch: **READY** (packages/env/chat/embed PASS). File restored to HEAD before scoring so `main.py` matches `origin/main`.
4. Entry: `python main.py "<question>"`, one question per process, ~2.5–5s each, all under 30s.

## Given G01–G16

| id | set | lv | lang | verdict | time | expected | actual |
|---|---|---|---|---|---|---|---|
| `G01` | given | 1 | en | pass | 2.7s | Additive manufacturing | Additive manufacturing. |
| `G02` | given | 1 | en | pass | 2.6s | Fused deposition modelling | Fused Deposition Modeling |
| `G03` | given | 1 | en | pass | 3.0s | The Faculty of Engineering | Faculty of Engineering. |
| `G04` | given | 2 | en | fail | 2.9s | 27 February 2026 | March 2, 2025. |
| `G05` | given | 2 | en | partial | 3.3s | PVC and polycarbonate | PVC, Teflon. |
| `G06` | given | 3 | en | fail | 2.5s | Smartsocks, Digitio, Gingtrolley | Unknown. |
| `G07` | given | 4 | en | fail | 4.0s | 7 | 5 |
| `G08` | given | 4 | en | fail | 4.5s | 31 | 3 |
| `G09` | given | 5 | en | pass | 2.9s | Innovation | Innovation. |
| `G10` | given | 1 | en | pass | 3.0s | Engineering | Faculty of Engineering |
| `G11` | given | 3 | en | fail | 3.8s | 11 | 8 |
| `G12` | given | 3 | en | fail | 2.9s | HKU ENGINEERING INNOVATION | BRAINSTORMING AREA |
| `G13` | given | 4 | en | partial | 2.9s | Faculty of Engineering; director name from indexed staff page or nameplate (not lab's Professor Amelia Reyes unless that is on the real site) | The Innovation Wing is managed by the Faculty of Engineering, and the director is not explicitly mentioned. |
| `G14` | given | 4 | en | fail | 4.5s | 31 | 3 |
| `G15` | given | 5 | en | fail | 3.3s | HKU ENGINEERING INNOVATION | TECHNOLOGIES AND INNOVATIONS |
| `G16` | given | 5 | en | fail | 3.1s | Electronics bench equipment (soldering stations, PSU, oscilloscope, hot-air rework) — confirm from the team's photo of Makerspace B. | 3 yellow rectangular containers or boxes. |

## Extra X01–X90

| id | set | lv | lang | verdict | time | expected | actual |
|---|---|---|---|---|---|---|---|
| `X01` | extra | 1 | zh | pass | 2.6s | Additive manufacturing | 增材制造 |
| `X02` | extra | 1 | zh | pass | 3.0s | Fused deposition modelling | 熔融沉积建模 |
| `X03` | extra | 1 | zh | pass | 3.1s | Faculty of Engineering | 工学院 |
| `X04` | extra | 2 | zh | partial | 3.1s | PVC and polycarbonate | PVC和特氟龙。 |
| `X05` | extra | 2 | zh | fail | 3.0s | 27 February 2026 | 2026年4月2日 |
| `X06` | extra | 3 | zh | fail | 2.7s | Smartsocks, Digitio, Gingtrolley | 1 |
| `X07` | extra | 4 | zh | fail | 4.2s | 7 | 3 |
| `X08` | extra | 4 | zh | fail | 3.8s | 31 | 3 |
| `X09` | extra | 5 | zh | fail | 2.5s | HKU ENGINEERING INNOVATION | 头脑风暴区 |
| `X10` | extra | 5 | zh | fail | 2.9s | Innovation | 科技 |
| `X11` | extra | 1 | en | pass | 2.9s | Fused deposition modelling | Fused Deposition Modeling |
| `X12` | extra | 1 | en | pass | 3.0s | Additive (additive manufacturing) | Additive. |
| `X13` | extra | 1 | zh | pass | 2.7s | Tam Wing Fan Innovation Wing | Tam Wing Fan Innovation Wing |
| `X14` | extra | 1 | en | pass | 3.1s | The University of Hong Kong (HKU) | The University of Hong Kong. |
| `X15` | extra | 1 | en | pass | 2.9s | Engineering and Technology | Engineering and Technology. |
| `X16` | extra | 1 | zh | pass | 3.0s | Students / undergraduates (entrusting and empowering students) | 学生 |
| `X17` | extra | 2 | en | pass | 3.2s | A project pitching event for students to present ideas and recruit teammates and academic advisors to form student interest groups. | Pitch New Tech Ideas is a project pitching event for students to present their project ideas, recruit teammates and academic advisors, and form student interest groups on various topics such as robotics, artificial intelligence, electric automobiles, and healthcare technologies. It helps improve students' ability to advocate ideas to a large audience and fosters community growth around their passions. |
| `X18` | extra | 2 | en | fail | 2.7s | Inspire, Equip and Showcase | Attracting talents, nurturing projects, and tackling engineering problems. |
| `X19` | extra | 2 | en | partial | 2.7s | Attracting and cultivating talents: scholars, researchers, industry leaders and influencers; an accelerator for inspiration and implementation. | Cultivating new generations of talents, not only scholars and researchers but also industry leaders and influencers. |
| `X20` | extra | 2 | en | fail | 3.6s | Design, Build and Fly; Engineering and Archaeology; HKU Racing; HKU Robocon | 4. Environmental Sustainability Group |
| `X21` | extra | 2 | zh | pass | 3.4s | Tam Wing Fan Innovation Fund and Philomathia Foundation Innovation Fund | Tam Wing Fan Innovation Fund 和 Philomathia Foundation Innovation Fund。 |
| `X22` | extra | 2 | en | pass | 2.7s | Gold Medal | Gold Medal |
| `X23` | extra | 2 | en | pass | 2.9s | ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals | ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals |
| `X24` | extra | 2 | en | pass | 2.9s | Third Class Honour in Treasure Hunter – Semi-Autonomous Mission; RAICOM National Final, August 2025, Hangzhou. | HKU RAICOM Robotics claimed Third Class Honour in the “Treasure Hunter – Semi-Autonomous Mission” category at the RAICOM National Final in August 2025 in Hangzhou. |
| `X25` | extra | 2 | en | pass | 3.6s | WeGoALGAE | WeGoALGAE |
| `X26` | extra | 2 | en | fail | 3.0s | Innogrow | The SRA team. |
| `X27` | extra | 2 | en | pass | 2.9s | Fourth place | Fourth place. |
| `X28` | extra | 2 | zh | pass | 3.2s | A showcase carnival at the end of every semester celebrating learning and creation; students demo projects and get feedback. | Engineering Inno Show 是一个展示创新工程学生项目的嘉年华活动，通常在每个学期末举办。 |
| `X29` | extra | 2 | en | fail | 3.1s | A student-run experiential activity to design, develop and teach a technology-related course under a Faculty Advisor; topics not covered in the formal curriculum. | A Student Initiated Course at Innovation Academy is a student-run experiential activity where students design, develop, and teach a course on a technology-related topic under the supervision of a Faculty Advisor. |
| `X30` | extra | 2 | en | pass | 2.8s | Robotics, artificial intelligence, electric automobiles and healthcare technologies | Robotics, artificial intelligence, electric automobiles, healthcare technologies. |
| `X31` | extra | 2 | zh | fail | 3.0s | Multidisciplinary Tutor Team – Broadest engineering skill coverage | 多学科的导师团队，涵盖广泛的工程技能。 |
| `X32` | extra | 2 | en | pass | 2.6s | Artificial intelligence, computer vision, electronics, and robotics | Artificial intelligence, computer vision, electronics, robotics. |
| `X33` | extra | 2 | en | fail | 3.0s | Contest gold for banned materials is PVC and polycarbonate (G05). Permitted in the lab page: acrylic, plywood and cardboard. | Acrylic and wood. |
| `X34` | extra | 2 | zh | fail | 3.0s | Lab gold: materials, components, consumables, equipment under $500; not travel, catering, salaries, software subscriptions. Confirm on the live funding page. | 不可以花在：运营费用、人员工资、宣传费用。 |
| `X35` | extra | 3 | en | fail | 2.7s | MAKERSPACE A | ON DUTY |
| `X36` | extra | 3 | en | fail | 4.1s | 4 | 2 |
| `X37` | extra | 3 | en | fail | 3.3s | Booking via portal | Booking required. |
| `X38` | extra | 3 | en | fail | 2.8s | Wooden / wooden tables | Wood. |
| `X39` | extra | 3 | zh | fail | 3.9s | 11 | 8 |
| `X40` | extra | 3 | en | fail | 4.3s | Eleven chairs (W2 slide 14 Prompt B). Confirm on the team's photo — spec example used 11 chairs and 11 tables. | 22 |
| `X41` | extra | 3 | en | fail | 4.1s | Two workbenches | 8 |
| `X42` | extra | 3 | en | fail | 2.6s | Read from the poster pixels (images.json has 01.-Design-Build-and-Fly-Team-2023-Poster-723x1024-1.png with empty alt). | "INDOOR MODEL AIRPLANE BUILD AND FLY" |
| `X43` | extra | 3 | en | fail | 2.9s | Digitio (image alt writes Digitoe) | The winner of Pitch New Tech Ideas 2025 selected for the 8th HKTDC Start-up Express is not specified. |
| `X44` | extra | 3 | en | fail | 4.0s | Whatever is visible on InnoWing-Logo.jpg — transcribe any wordmark exactly. | The Innovation Wing logo image contains a text and mark. |
| `X45` | extra | 3 | zh | fail | 2.8s | Historic first championship representing Hong Kong (alt: clinches historic first championship). | 胜利获得首个冠军。 |
| `X46` | extra | 3 | en | fail | 3.1s | cllinches (double l) in 'HKU Robocon cllinches back-to-back victory…' | "Robocon 2025" is a typo that refers to the year instead of 2026. |
| `X47` | extra | 3 | en | fail | 3.0s | HKU ENGINEERING INNOVATION (write [unreadable] for any glyph you cannot see — W2 instruction) | "Tam Wing Fan Inno Wing Two" "FACULTY OF ENGINEERING" |
| `X48` | extra | 3 | zh | fail | 3.3s | Along the north wall; spatial relation as in the team's photo (W2 example: printers along the north wall, tables in the room). | 在桌子的右侧、对着左侧窗户的墙。 |
| `X49` | extra | 3 | en | fail | 2.9s | AI workshop - Build you ChatBot | AI IN SIGHT - A 2-HOUR HANDS-ON WORKSHOP WITH HUSKYLENS. |
| `X50` | extra | 3 | en | fail | 3.2s | OCR/transcription of the poster (second, text-only description pass — W2 slide 16). | "Registration", "Details" |
| `X51` | extra | 4 | en | partial | 2.9s | Faculty of Engineering + director from staff/nameplate. W2 split example uses this longer name in sub-question 1. | Faculty of Engineering; the director is not specified. |
| `X52` | extra | 4 | zh | partial | 3.2s | 学院 Faculty of Engineering；主任需真站/铭牌。不要用 lab 的 Professor Amelia Reyes 除非真站如此。 | 工学院，主任是 Norman Tien 教授。 |
| `X53` | extra | 4 | en | fail | 4.0s | Lab split: 4× Prusa MK4, 2× Bambu X1C, 1× Formlabs Form 4, total 7. Confirm against the real equipment page/photos. | 4 |
| `X54` | extra | 4 | en | fail | 4.0s | Lab: 6 FDM (4 Prusa + 2 Bambu) and 1 resin (Form 4). Total still 7. | 3 |
| `X55` | extra | 4 | zh | fail | 4.2s | Lab: A 40, B 24; individuals use B drop-in desks. Verify on real venue pages/photos. | Makerspace A 的容量是 20 人，Makerspace B 的容量是 15 人。Makerspace B 适合个人不预约进场。 |
| `X56` | extra | 4 | en | fail | 4.1s | At least HKU Racing and HKU Robocon (2). Design, Build and Fly is also a competition team — count 3 if the team includes DBF; say which rule you used. | 4 |
| `X57` | extra | 4 | en | fail | 3.9s | Count the named entities in that paragraph (HKU Engineering Team/Robocon, SRA/ACTalyse, iGEM, RAICOM Robotics, Digitoe, WeGoALGAE, Innogrow, RoboMaster) — about 8. List them then count. | 6 |
| `X58` | extra | 4 | en | fail | 3.0s | 2025: iGEM gold, RAICOM (Aug 2025 Hangzhou), Pitch New Tech Ideas / HKTDC, Hult Prize 2025, RMUL. 2026: Robocon Hong Kong 2026, ABU Robocon championship item dated 2026 in image URLs. List evidence by year. | 2026: 0 |
| `X59` | extra | 4 | zh | fail | 2.7s | Inno Show: end of every semester. Pitch: form student interest groups (recruit teammates and advisors). | Inno Show 在每学期的末尾举行；Pitch New Tech Ideas 用来组建团队。 |
| `X60` | extra | 4 | en | fail | 4.0s | 26 images, 11 with alt (inventory at the time this set was written). Re-count from the JSON if rebuilt. | 10 |
| `X61` | extra | 4 | en | fail | 3.1s | Lab: teams of three or more book A; B has six drop-in desks without booking. Confirm live. | Members may book Makerspace A. In Makerspace B, tools and equipment may be used without a booking, but specific details are unclear. |
| `X62` | extra | 4 | en | fail | 2.8s | Need both the total-7 chunk and the north-wall-4 image description. If photos show printers in A that are the same print-room bank, 7 is inclusive; if A has a separate row, totals change. List evidence; do not guess. | Yes. |
| `X63` | extra | 5 | zh | fail | 2.8s | HKU ENGINEERING INNOVATION | BRAINSTORMING AREA |
| `X64` | extra | 5 | en | fail | 3.6s | Lab: four mobile whiteboards along the back wall; seating in front. Confirm from aerial photo. | They are located behind the seating area. |
| `X65` | extra | 5 | en | fail | 3.7s | Four (lab). Count from the photo, not from memory of the lab page if you are testing Lv5. | 3 |
| `X66` | extra | 5 | zh | fail | 3.7s | Lab: 2 soldering stations, 1 bench power supply, 1 two-channel oscilloscope, 1 hot air rework station. Photograph to confirm. | 在 Makerspace B 靠窗的 electronics bench 上有 1 台黑色显示器，1 台黑色键盘，1 台黑色鼠标，1 台白色和黑色的台式秤，1 个黄色锐器容器，1 个蓝色的移液器架，1 台白色和蓝色的漩涡混合器。 |
| `X67` | extra | 5 | en | fail | 3.3s | Whatever the photo shows (W2 example mentioned colourful cubic sofas / a large blue sign). Copy colours only if they identify the object. | Brown fabric or leather. |
| `X68` | extra | 5 | en | fail | 3.9s | Only from photographs of the gallery board. Lab news page says winners are on that board and not listed in the article. | I can't provide specific names for the awards or teams listed on the award board in the gallery outside the office, but I would guess that they could include notable recognitions like "Innovation Award" or "Best Design" associated with the Tam Wing Fan Innovation Wing. |
| `X69` | extra | 5 | zh | fail | 3.1s | Transcribe from gallery photos. Do not invent from Academy homepage achievements. | "HKUR", "HKU ROBOCON TEAM", "ENGINEERING", "HKU ROBOTICS TEAM". |
| `X70` | extra | 5 | en | fail | 3.3s | Read labels off the photographed floor plan. Lab gallery-index.txt says a floor plan hangs there. | MACHINE SHOP, ELECTRONIC WORKBENCH, MEETING ROOM, OFFICE, THEMATIC WORKSHOP, LASER CUTTING AND ENGRAVING MACHINE, SAFETY CORNER. |
| `X71` | extra | 5 | en | fail | 4.3s | Lab: a bank of tool lockers along the east wall. Count banks from makerspace.JPG / Makerspace close up.JPG. | 2 |
| `X72` | extra | 5 | zh | fail | 3.0s | Lab page: HDMI or USB-C. Prefer sticker/label on the display if photographed. | 信息未提供，猜测使用USB和HDMI接口。 |
| `X73` | extra | 5 | en | fail | 3.1s | Exact poster/door text from the team's zone photos. Use [unreadable] rather than guess. | I cannot provide the exact text of safety or booking notices. However, I can summarize that members must follow safety protocols and confirm booking details beforehand. |
| `X74` | extra | 5 | en | fail | 4.2s | Count from Labs/images/makerspace.JPG and close-up; gold if fully visible is 11 (spec). | 9 |
| `X75` | extra | 5 | en | fail | 3.0s | Do not answer from Lv5 photos — Event Hall is OUT of collection scope (W2 slide 27). If a website page exists: lab says 180 seats, lectern mic + four radio mics. | 40 seats; Hand-held x 6, Clip mic x 2. |
| `X76` | extra | 5 | zh | fail | 2.8s | Out of Lv5 collection scope (machine workshop excluded). Only answer if the official websites publish it (then it is Lv2). | 1440D |
| `X77` | extra | 3 | en | fail | 4.0s | A generic caption is a FAILED answer for scoring. The useful answer is the five-field extraction (location, counts, verbatim text, spatial, identifying colours). | Makerspace A features a bright, open interior with a white glossy floor and exposed gray ceiling. It contains 8 light-wood-topped high workbench tables with white metal legs and caster wheels, surrounded by approximately 22 round dark-brown/black stools. The space includes a black monitor, two dark machine units, and several objects on tables like a notice sign and pump bottles. Large floor-to-ceiling windows provide outdoor views, while a glass-walled room is visible in the background. The color scheme includes light birch wood, white, dark tones, and teal accents. |
| `X78` | extra | 1 | en | pass | 2.9s | The Faculty of Engineering | Faculty of Engineering |
| `X79` | extra | 4 | en | partial | 3.4s | Same two facts as G13, reversed order. Faculty of Engineering + director. | Professor Norman Tien, Faculty of Engineering. |
| `X80` | extra | 2 | en | fail | 4.0s | Visit our Engineering Inno Show is a heading with empty body on innowing1; Academy page calls it a showcase carnival at end of semester. | A showcase carnival that celebrates innovative Engineering student projects. |
| `X81` | extra | 1 | zh | pass | 3.0s | Fused deposition modelling | Fused Deposition Modeling |
| `X82` | extra | 2 | en | pass | 3.9s | Flexible: talks, one-on-one dialogue, or panel discussion, with guest speakers (entrepreneurs, industry partners, researchers, alumni). | Talks, one-on-one dialogue, panel discussion. |
| `X83` | extra | 2 | en | pass | 3.3s | The writer-in-residence concept, for exchange on advanced technologies / research from Faculty of Engineering projects. | It is borrowed from the concept of a writer-in-residence. |
| `X84` | extra | 2 | zh | fail | 3.2s | Prestigious universities and cutting-edge companies; latest technology and robotics R&D. | 先进技术和创新研发的大学与公司。 |
| `X85` | extra | 3 | en | fail | 3.2s | HKU ENGINEERING INNOVATION | BRAINSTORMING AREA |
| `X86` | extra | 4 | en | fail | 5.0s | 31, plus any one indexed poster title. The integer is not written on the site. | 2 |
| `X87` | extra | 5 | en | fail | 3.0s | Lab: small parts store in the cupboard by the door. Confirm photographically. | To the right of the door. |
| `X88` | extra | 5 | zh | fail | 3.3s | Lab gallery page: open whenever the building is open. Prefer the physical sign if present. | 画廊在办公时间以外不开放。现场指示牌应为：“非开放时间，请勿进入。” |
| `X89` | extra | 4 | en | fail | 4.5s | Faculty of Engineering; 7 printers. | 3 |
| `X90` | extra | 3 | en | fail | 4.0s | Transcribe stickers from Labs/images/Makerspace close up.JPG (practice) or team photos. | 'EMERGENCY STOP', 'PLEASE CLEAN MACHINE AFTER EACH USE', 'WARNING', '警告'. |

## By level

| level | pass | partial | fail | n |
|---|---|---|---|---|
| Lv1 | 15 | 0 | 0 | 15 |
| Lv2 | 11 | 4 | 11 | 26 |
| Lv3 | 0 | 0 | 23 | 23 |
| Lv4 | 0 | 4 | 17 | 21 |
| Lv5 | 1 | 0 | 20 | 21 |

## Notes on given misses

- G04 expected 27 February 2026; model said March 2, 2025.
- G05 PVC only (said Teflon, not polycarbonate).
- G06/G07/G08/G11/G14 counts and Pitch winners wrong or Unknown.
- G12/G15 wall text: model said BRAINSTORMING AREA / TECHNOLOGIES AND INNOVATIONS, not HKU ENGINEERING INNOVATION.
- G13 faculty OK, director not named.
- G16 window bench: yellow boxes, not electronics gear.

## Checkout

```text
git clone --branch main --single-branch \
  https://github.com/aomuy/ChatbotChallenge2026Team16.git
HEAD = aad6dc9e816d3186ce456d198c16d19a5deb0290
```

Working tree dirty only as `submission_repo/data/chroma/chroma.sqlite3` (index use). `.env` untracked/ignored.
