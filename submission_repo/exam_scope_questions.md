# Exam-scope questions (given + extra)

Additive set for Chatbot Challenge 2026. **Does not replace** `dev_set.json`.

Counts: **16 given** + **90 extra** = **106 total** (en 76, zh 30).

By level: Lv1=15, Lv2=26, Lv3=23, Lv4=21, Lv5=21.

Machine-readable twin: [`exam_scope_questions.json`](exam_scope_questions.json).

## How to run

```bash
cd submission_repo
# given stems only (official/spec wording):
python3 - <<'PY'
import json, subprocess, sys
qs=[q['question'] for q in json.load(open('exam_scope_questions.json'))['questions'] if q['set']=='given']
subprocess.run([sys.executable,'main.py',*qs], check=False)
PY
```

Same contract as the grader: `python main.py "question"`, 30s/question, one stdout line, no invented API keys.

## Scope reminder

- Lv1 general knowledge; Lv2 website text; Lv3 image-only; Lv4 not written anywhere (count/compound); Lv5 physical (gallery, posters, venues, equipment).
- Lv5 collection **excludes** machine workshop and event hall (`X75`, `X76`).
- Gold in `given` rows is official. Extra expected notes may cite `Labs/sample_corpus` as **practice only**.

## Given (keep verbatim)

| id | set | lv | lang | question | expected | source |
|---|---|---|---|---|---|---|
| `G01` | given | Lv1 | en | What is 3D printing also known as? | Additive manufacturing | dev_set.json |
| `G02` | given | Lv1 | en | What does FDM stand for in 3D printing? | Fused deposition modelling | dev_set.json |
| `G03` | given | Lv1 | en | Which faculty would you expect an engineering innovation centre to belong to? | The Faculty of Engineering | dev_set.json |
| `G04` | given | Lv2 | en | When was the deadline for the second round of the Funding Scheme in 2025-26? | 27 February 2026 | dev_set.json |
| `G05` | given | Lv2 | en | Which two materials are banned from the laser cutter? | PVC and polycarbonate | dev_set.json |
| `G06` | given | Lv3 | en | What were the winning teams in Pitch New Tech Ideas in 2025? | Smartsocks, Digitio, Gingtrolley | dev_set.json |
| `G07` | given | Lv4 | en | How many 3D printers does the Centre run in total? | 7 | dev_set.json |
| `G08` | given | Lv4 | en | How many workshop posters are on the Innovation Academy websites for 2025? | 31 | dev_set.json |
| `G09` | given | Lv5 | en | On the wall at the back of the brainstorming area, there are three words. HKU, Engineering, and...? | Innovation | dev_set.json |
| `G10` | given | Lv1 | en | What faculty does the Tam Wing Fan Innovation Wing belong to? | Engineering | W0_Setup_and_Rules.pptx |
| `G11` | given | Lv3 | en | How many tables are in Makerspace A? | 11 | W2 published spec (slide 11–12) |
| `G12` | given | Lv3 | en | What three words are on the wall behind the brainstorming area? | HKU ENGINEERING INNOVATION | W2 published spec (slide 11–12) |
| `G13` | given | Lv4 | en | Which faculty runs the Innovation Wing, and who is its director? | Faculty of Engineering; director name from indexed staff page or nameplate (not lab's Professor Amelia Reyes unless that is on the real site) | W2 slide 19/24 |
| `G14` | given | Lv4 | en | How many workshop posters are on the Innovation Academy website for 2025? | 31 | W2 slide 20 |
| `G15` | given | Lv5 | en | What three words are on the wall behind the seating? | HKU ENGINEERING INNOVATION | Labs/lab4_description_prompt.ipynb |
| `G16` | given | Lv5 | en | What is on the bench by the window? | Electronics bench equipment (soldering stations, PSU, oscilloscope, hot-air rework) — confirm from the team's photo of Makerspace B. | Labs/lab4_description_prompt.ipynb |

## Extra

| id | set | lv | lang | question | expected | source |
|---|---|---|---|---|---|---|
| `X01` | extra | Lv1 | zh | 3D 打印也被称为什么？ | Additive manufacturing | G01 zh mirror |
| `X02` | extra | Lv1 | zh | 在 3D 打印里，FDM 代表什么？ | Fused deposition modelling | G02 zh |
| `X03` | extra | Lv1 | zh | Tam Wing Fan Innovation Wing 属于哪个学院？ | Faculty of Engineering | G10 zh |
| `X04` | extra | Lv2 | zh | 激光切割机禁止使用哪两种材料？ | PVC and polycarbonate | G05 zh |
| `X05` | extra | Lv2 | zh | 2025-26 学年 Funding Scheme 第二轮截止日期是哪一天？ | 27 February 2026 | G04 zh |
| `X06` | extra | Lv3 | zh | 2025 年 Pitch New Tech Ideas 的优胜队伍有哪些？ | Smartsocks, Digitio, Gingtrolley | G06 zh |
| `X07` | extra | Lv4 | zh | 中心一共运行多少台 3D 打印机？ | 7 | G07 zh |
| `X08` | extra | Lv4 | zh | 2025 年 Innovation Academy 网站上有多少张 workshop 海报？ | 31 | G14 zh |
| `X09` | extra | Lv5 | zh | 头脑风暴区后方墙上的三个词是什么？ | HKU ENGINEERING INNOVATION | G12 zh |
| `X10` | extra | Lv5 | zh | 在头脑风暴区后方的墙上有三个词。HKU、Engineering，以及……？ | Innovation | G09 zh |
| `X11` | extra | Lv1 | en | What does the abbreviation FDM expand to? | Fused deposition modelling | lv1 paraphrase |
| `X12` | extra | Lv1 | en | Is 3D printing a subtractive or additive process? | Additive (additive manufacturing) | lv1 |
| `X13` | extra | Lv1 | zh | 港大 Tam Wing Fan Innovation Wing 的英文全称是什么？ | Tam Wing Fan Innovation Wing | lv1 name |
| `X14` | extra | Lv1 | en | Which university houses the Tam Wing Fan Innovation Wing? | The University of Hong Kong (HKU) | lv1/lv2 |
| `X15` | extra | Lv1 | en | What academic fields does Inno Wing say it promotes interdisciplinary innovation in? | Engineering and Technology | pages.json About Inno Wing |
| `X16` | extra | Lv1 | zh | Inno Wing 的教育目标 Educational Aim 强调把项目交给谁来主导？ | Students / undergraduates (entrusting and empowering students) | lv2-ish but general |
| `X17` | extra | Lv2 | en | What is Pitch New Tech Ideas according to Innovation Academy? | A project pitching event for students to present ideas and recruit teammates and academic advisors to form student interest groups. | pages.json |
| `X18` | extra | Lv2 | en | What three goals do Innovation Academy programmes capture? | Inspire, Equip and Showcase | pages.json |
| `X19` | extra | Lv2 | en | What does the Innovation Academy say it is a hub for? | Attracting and cultivating talents: scholars, researchers, industry leaders and influencers; an accelerator for inspiration and implementation. | pages.json |
| `X20` | extra | Lv2 | en | Name the four student interest groups listed on the Innovation Wing One page. | Design, Build and Fly; Engineering and Archaeology; HKU Racing; HKU Robocon | pages.json SIG headings |
| `X21` | extra | Lv2 | zh | Innovation Academy 的 Funding Scheme 用的是哪两个基金的名字？ | Tam Wing Fan Innovation Fund and Philomathia Foundation Innovation Fund | pages.json |
| `X22` | extra | Lv2 | en | What medal did HKU iGEM win at the 2025 iGEM Competition? | Gold Medal | pages.json Student Achievements |
| `X23` | extra | Lv2 | en | Which project did the SRA team win the HKAE Pitch Competition with? | ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals | pages.json |
| `X24` | extra | Lv2 | en | What result did HKU RAICOM Robotics achieve, in which category, and where/when was the national final? | Third Class Honour in Treasure Hunter – Semi-Autonomous Mission; RAICOM National Final, August 2025, Hangzhou. | pages.json |
| `X25` | extra | Lv2 | en | Which Student Interest Group was selected for the Hult Prize 2025 Incubator Programme? | WeGoALGAE | pages.json / images.json alt |
| `X26` | extra | Lv2 | en | Who was crowned champion at the HKAE Pitch Competition on Grand Challenge Engineering Topics for University Students 2024-25? | Innogrow | images.json alt |
| `X27` | extra | Lv2 | en | What place did RoboMaster achieve at the RMUL Zhejiang Station competition? | Fourth place | pages.json |
| `X28` | extra | Lv2 | zh | Engineering Inno Show 是什么活动、在什么时候举办？ | A showcase carnival at the end of every semester celebrating learning and creation; students demo projects and get feedback. | pages.json |
| `X29` | extra | Lv2 | en | What is a Student Initiated Course at Innovation Academy? | A student-run experiential activity to design, develop and teach a technology-related course under a Faculty Advisor; topics not covered in the formal curriculum. | pages.json |
| `X30` | extra | Lv2 | en | What topics does Pitch New Tech Ideas list as example SIG areas? | Robotics, artificial intelligence, electric automobiles and healthcare technologies | pages.json |
| `X31` | extra | Lv2 | zh | Innovation Wing Tutor 团队用一句话怎么描述自己？ | Multidisciplinary Tutor Team – Broadest engineering skill coverage | pages.json |
| `X32` | extra | Lv2 | en | What intern skill areas does Student Development Projects mention? | Artificial intelligence, computer vision, electronics, and robotics | pages.json |
| `X33` | extra | Lv2 | en | Which two materials may be cut on the laser cutter in the sample equipment page? | Contest gold for banned materials is PVC and polycarbonate (G05). Permitted in the lab page: acrylic, plywood and cardboard. | Labs/sample_corpus/equipment-laser-cutter.txt (lab) / real equipment pages |
| `X34` | extra | Lv2 | zh | Funding Scheme 的钱可以花在什么上、不可以花在什么上？（若网页有清单） | Lab gold: materials, components, consumables, equipment under $500; not travel, catering, salaries, software subscriptions. Confirm on the live funding page. | lab corpus / real funding page |
| `X35` | extra | Lv3 | en | What exact text is on the sign above the door of Makerspace A? | MAKERSPACE A | W2 slide 14 |
| `X36` | extra | Lv3 | en | How many 3D printers stand along the north wall of Makerspace A? | 4 | W2 slide 11 |
| `X37` | extra | Lv3 | en | What does the whiteboard in Makerspace A say about booking? | Booking via portal | W2 slide 11 |
| `X38` | extra | Lv3 | en | What material are the four-person tables in Makerspace A? | Wooden / wooden tables | W2 slide 11 |
| `X39` | extra | Lv3 | zh | Makerspace A 里有多少张桌子？ | 11 | W2 spec zh |
| `X40` | extra | Lv3 | en | How many chairs are in Makerspace A in the workshop example extraction? | Eleven chairs (W2 slide 14 Prompt B). Confirm on the team's photo — spec example used 11 chairs and 11 tables. | W2 slide 14 |
| `X41` | extra | Lv3 | en | How many workbenches does the W2 example description record in Makerspace A? | Two workbenches | W2 slide 14 |
| `X42` | extra | Lv3 | en | What is the title text on the Design, Build and Fly 2023 poster hosted on Innovation Wing? | Read from the poster pixels (images.json has 01.-Design-Build-and-Fly-Team-2023-Poster-723x1024-1.png with empty alt). | data/images.json |
| `X43` | extra | Lv3 | en | Which Pitch New Tech Ideas 2025 winner was selected for the 8th HKTDC Start-up Express? | Digitio (image alt writes Digitoe) | data/images.json |
| `X44` | extra | Lv3 | en | What does the Innovation Wing logo image contain (text or mark)? | Whatever is visible on InnoWing-Logo.jpg — transcribe any wordmark exactly. | data/images.json |
| `X45` | extra | Lv3 | zh | HKU Robocon 在 ABU Robocon 为香港取得了什么历史成绩？（以成就图/说明为准） | Historic first championship representing Hong Kong (alt: clinches historic first championship). | images.json alt |
| `X46` | extra | Lv3 | en | What typo appears in the Robocon Hong Kong 2026 image alt text? | cllinches (double l) in 'HKU Robocon cllinches back-to-back victory…' | images.json |
| `X47` | extra | Lv3 | en | Transcribe every word visible on the wall behind the brainstorming seating, in order. | HKU ENGINEERING INNOVATION (write [unreadable] for any glyph you cannot see — W2 instruction) | W2 slide 12 |
| `X48` | extra | Lv3 | zh | Makerspace A 北墙的 3D 打印机在桌子的哪一侧、对着什么？ | Along the north wall; spatial relation as in the team's photo (W2 example: printers along the north wall, tables in the room). | W2 schema |
| `X49` | extra | Lv3 | en | Copy the alt text of the AI workshop image on the Innovation Academy homepage. | AI workshop - Build you ChatBot | data/images.json |
| `X50` | extra | Lv3 | en | Describe only the visible text on the 2023 Design-Build-and-Fly poster, not the layout. | OCR/transcription of the poster (second, text-only description pass — W2 slide 16). | W2 slides 16–17 |
| `X51` | extra | Lv4 | en | Which faculty runs the Tam Wing Fan Innovation Wing, and who is its director? | Faculty of Engineering + director from staff/nameplate. W2 split example uses this longer name in sub-question 1. | W2 slide 24 |
| `X52` | extra | Lv4 | zh | 哪个学院运营 Innovation Wing，主任是谁？ | 学院 Faculty of Engineering；主任需真站/铭牌。不要用 lab 的 Professor Amelia Reyes 除非真站如此。 | W2 zh |
| `X53` | extra | Lv4 | en | List each 3D printer model the Centre runs and the count per model, then the total. | Lab split: 4× Prusa MK4, 2× Bambu X1C, 1× Formlabs Form 4, total 7. Confirm against the real equipment page/photos. | dev_set G07 + lab equipment table |
| `X54` | extra | Lv4 | en | How many FDM printers and how many resin printers does the Centre run? | Lab: 6 FDM (4 Prusa + 2 Bambu) and 1 resin (Form 4). Total still 7. | lab equipment-3d-printers.txt |
| `X55` | extra | Lv4 | zh | Makerspace A 和 Makerspace B 的容量分别是多少人？哪个适合个人不预约进场？ | Lab: A 40, B 24; individuals use B drop-in desks. Verify on real venue pages/photos. | lab venues pages |
| `X56` | extra | Lv4 | en | How many of the homepage SIG names refer to student racing or robot competitions? | At least HKU Racing and HKU Robocon (2). Design, Build and Fly is also a competition team — count 3 if the team includes DBF; say which rule you used. | pages.json SIG headings |
| `X57` | extra | Lv4 | en | Among the Student Achievements on the Innovation Academy homepage, how many distinct teams or projects are named? | Count the named entities in that paragraph (HKU Engineering Team/Robocon, SRA/ACTalyse, iGEM, RAICOM Robotics, Digitoe, WeGoALGAE, Innogrow, RoboMaster) — about 8. List them then count. | pages.json Student Achievements |
| `X58` | extra | Lv4 | en | Which achievements on the Academy site happened in 2025, and which in 2026? | 2025: iGEM gold, RAICOM (Aug 2025 Hangzhou), Pitch New Tech Ideas / HKTDC, Hult Prize 2025, RMUL. 2026: Robocon Hong Kong 2026, ABU Robocon championship item dated 2026 in image URLs. List evidence by year. | pages.json / images.json dates |
| `X59` | extra | Lv4 | zh | 同时回答：Inno Show 在每学期什么时候举行，以及 Pitch New Tech Ideas 用来组建什么？ | Inno Show: end of every semester. Pitch: form student interest groups (recruit teammates and advisors). | pages.json |
| `X60` | extra | Lv4 | en | How many images are currently recorded in submission_repo/data/images.json, and how many of those have non-empty alt text? | 26 images, 11 with alt (inventory at the time this set was written). Re-count from the JSON if rebuilt. | data/images.json |
| `X61` | extra | Lv4 | en | Compare Makerspace A booking rules with Makerspace B: who may book A, and what can you use in B without a booking? | Lab: teams of three or more book A; B has six drop-in desks without booking. Confirm live. | lab venues |
| `X62` | extra | Lv4 | en | Does the Centre's 7 printers figure include the four along Makerspace A's north wall, or are those extra? Explain from evidence. | Need both the total-7 chunk and the north-wall-4 image description. If photos show printers in A that are the same print-room bank, 7 is inclusive; if A has a separate row, totals change. List evidence; do not guess. | W2 + dev_set |
| `X63` | extra | Lv5 | zh | 站在头脑风暴区座位区，背后墙上三个英文词从左到右原文是什么？ | HKU ENGINEERING INNOVATION | W2 Lv5 + lab images |
| `X64` | extra | Lv5 | en | Where are the mobile whiteboards in the brainstorming area relative to the seating? | Lab: four mobile whiteboards along the back wall; seating in front. Confirm from aerial photo. | lab venues-brainstorming-area.txt + Brainstorming aerial.JPG |
| `X65` | extra | Lv5 | en | How many mobile whiteboards are kept in the brainstorming area? | Four (lab). Count from the photo, not from memory of the lab page if you are testing Lv5. | physical / lab |
| `X66` | extra | Lv5 | zh | Makerspace B 靠窗的 electronics bench 上有哪些仪器、各几台？ | Lab: 2 soldering stations, 1 bench power supply, 1 two-channel oscilloscope, 1 hot air rework station. Photograph to confirm. | lab equipment-electronics-bench.txt |
| `X67` | extra | Lv5 | en | What colour and material identify the sofas or seating in the brainstorming area in your photos? | Whatever the photo shows (W2 example mentioned colourful cubic sofas / a large blue sign). Copy colours only if they identify the object. | W2 DESCRIPTION_PROMPT example |
| `X68` | extra | Lv5 | en | What award names and team names are on the award board in the gallery outside the office? | Only from photographs of the gallery board. Lab news page says winners are on that board and not listed in the article. | W2 slide 27 + lab news-2025-awards.txt |
| `X69` | extra | Lv5 | zh | 办公室外走廊 gallery 里，当前奖项板/展示照片上能逐字读到哪些队名？ | Transcribe from gallery photos. Do not invent from Academy homepage achievements. | W2 slide 27 |
| `X70` | extra | Lv5 | en | On the building floor plan in the gallery, which rooms are labelled besides the makerspaces? | Read labels off the photographed floor plan. Lab gallery-index.txt says a floor plan hangs there. | lab gallery-index.txt |
| `X71` | extra | Lv5 | en | Where are the tool lockers in Makerspace A, and how many banks/rows are visible? | Lab: a bank of tool lockers along the east wall. Count banks from makerspace.JPG / Makerspace close up.JPG. | lab + Labs/images |
| `X72` | extra | Lv5 | zh | Makerspace A 北墙大屏能用哪些接口连接笔记本？（若现场贴纸/铭牌有写） | Lab page: HDMI or USB-C. Prefer sticker/label on the display if photographed. | venues-makerspace-a.txt / photo |
| `X73` | extra | Lv5 | en | Copy any safety or booking notice posted on the door or wall of Makerspace A or B, word for word. | Exact poster/door text from the team's zone photos. Use [unreadable] rather than guess. | W2 schema field 3 |
| `X74` | extra | Lv5 | en | How many work tables are visible in your Makerspace A photographs, and does that match eleven? | Count from Labs/images/makerspace.JPG and close-up; gold if fully visible is 11 (spec). | W2 spec + lab photos |
| `X75` | extra | Lv5 | en | What is the seating capacity of the Event Hall, and which microphones does it have? | Do not answer from Lv5 photos — Event Hall is OUT of collection scope (W2 slide 27). If a website page exists: lab says 180 seats, lectern mic + four radio mics. | W2 slide 27 exclusion |
| `X76` | extra | Lv5 | zh | Machine workshop / 金工车间的床身尺寸或设备型号是什么？ | Out of Lv5 collection scope (machine workshop excluded). Only answer if the official websites publish it (then it is Lv2). | W2 slide 27 |
| `X77` | extra | Lv3 | en | Describe this image of Makerspace A. | A generic caption is a FAILED answer for scoring. The useful answer is the five-field extraction (location, counts, verbatim text, spatial, identifying colours). | W2 slide 14 Prompt A |
| `X78` | extra | Lv1 | en | Which faculty would you expect an engineering innovation centreto belong to? | The Faculty of Engineering | dev_set.json command field |
| `X79` | extra | Lv4 | en | Name the director of the Innovation Wing, and which faculty runs it? (director first) | Same two facts as G13, reversed order. Faculty of Engineering + director. | W2 slide 24 |
| `X80` | extra | Lv2 | en | What is the Engineering Inno Show described as on the Innovation Wing site? | Visit our Engineering Inno Show is a heading with empty body on innowing1; Academy page calls it a showcase carnival at end of semester. | pages.json both sites |
| `X81` | extra | Lv1 | zh | FDM 3D 打印的中文里常说的熔融沉积，对应的英文全称是什么？ | Fused deposition modelling | dev_set G02 |
| `X82` | extra | Lv2 | en | What format can Innovation Academy Sharings take? | Flexible: talks, one-on-one dialogue, or panel discussion, with guest speakers (entrepreneurs, industry partners, researchers, alumni). | pages.json |
| `X83` | extra | Lv2 | en | What is the Hands-on workshop programme borrowed from, conceptually? | The writer-in-residence concept, for exchange on advanced technologies / research from Faculty of Engineering projects. | pages.json |
| `X84` | extra | Lv2 | zh | Study Tour 带学生去看什么？ | Prestigious universities and cutting-edge companies; latest technology and robotics R&D. | pages.json |
| `X85` | extra | Lv3 | en | What three words appear behind the brainstorming area: copy them in ALL CAPS as on the wall. | HKU ENGINEERING INNOVATION | W2 |
| `X86` | extra | Lv4 | en | How many workshop posters for 2025 are on the Innovation Academy site, and name one of them if your index stores titles. | 31, plus any one indexed poster title. The integer is not written on the site. | W2 + G08 |
| `X87` | extra | Lv5 | en | In Makerspace B, where is the parts store / consumables cupboard relative to the door? | Lab: small parts store in the cupboard by the door. Confirm photographically. | venues-makerspace-b.txt |
| `X88` | extra | Lv5 | zh | gallery 走廊是否在办公时间以外开放？现场指示牌怎么写？ | Lab gallery page: open whenever the building is open. Prefer the physical sign if present. | gallery-index.txt |
| `X89` | extra | Lv4 | en | Which faculty runs Inno Wing and how many 3D printers does the Centre run? | Faculty of Engineering; 7 printers. | G10+G07 |
| `X90` | extra | Lv3 | en | From the Makerspace close-up photo, what labels or stickers are readable on the equipment? | Transcribe stickers from Labs/images/Makerspace close up.JPG (practice) or team photos. | Labs/images/Makerspace close up.JPG |

## Notes by id

### G01 · Lv1 · given

- **Question:** What is 3D printing also known as?
- **Expected:** Additive manufacturing
- **Notes:** Official gold in submission_repo/dev_set.json.
- **Why in scope:** Lv1 general knowledge; grader command in dev_set.json.

### G02 · Lv1 · given

- **Question:** What does FDM stand for in 3D printing?
- **Expected:** Fused deposition modelling
- **Notes:** Official gold. British spelling modelling.
- **Why in scope:** Lv1; official dev set.

### G03 · Lv1 · given

- **Question:** Which faculty would you expect an engineering innovation centre to belong to?
- **Expected:** The Faculty of Engineering
- **Notes:** Official gold. W0 CLI example is a close variant.
- **Why in scope:** Lv1; official dev set.

### G04 · Lv2 · given

- **Question:** When was the deadline for the second round of the Funding Scheme in 2025-26?
- **Expected:** 27 February 2026
- **Notes:** Official gold. Labs/sample_corpus/funding-scheme.txt says 20 February 2026 — do not use the lab date.
- **Why in scope:** Lv2 text retrieval on the real sites / official gold.

### G05 · Lv2 · given

- **Question:** Which two materials are banned from the laser cutter?
- **Expected:** PVC and polycarbonate
- **Notes:** Official gold. Lab laser-cutter page matches, but contest gold is this pair.
- **Why in scope:** Lv2 equipment safety fact buried in text.

### G06 · Lv3 · given

- **Question:** What were the winning teams in Pitch New Tech Ideas in 2025?
- **Expected:** Smartsocks, Digitio, Gingtrolley
- **Notes:** Official Lv3 gold. Page body does not list all three; images/alt may say Digitoe.
- **Why in scope:** Lv3 visual: answer lives in an image (or its alt), not the programme blurb.
- **Failure mode:** A/B/C never collected/described; alt typo Digitoe vs Digitio

### G07 · Lv4 · given

- **Question:** How many 3D printers does the Centre run in total?
- **Expected:** 7
- **Notes:** Official Lv4 gold. May be split across a table (4+2+1 in the lab corpus).
- **Why in scope:** Lv4 counting/aggregation; number may not sit in one chunk.

### G08 · Lv4 · given

- **Question:** How many workshop posters are on the Innovation Academy websites for 2025?
- **Expected:** 31
- **Notes:** Official gold. W2: no chunk contains the number 31; must count the set. k=5 cannot succeed.
- **Why in scope:** Lv4 counting over a filtered set; W2 slide 20.
- **Failure mode:** semantic search k ceiling

### G09 · Lv5 · given

- **Question:** On the wall at the back of the brainstorming area, there are three words. HKU, Engineering, and...?
- **Expected:** Innovation
- **Notes:** Official Lv5 gold. Full three words are HKU ENGINEERING INNOVATION. Paraphrase scores zero.
- **Why in scope:** Lv5 physical / verbatim wall text; published spec family.
- **Failure mode:** caption instead of exact copy

### G10 · Lv1 · given

- **Question:** What faculty does the Tam Wing Fan Innovation Wing belong to?
- **Expected:** Engineering
- **Notes:** W0_Setup_and_Rules.pptx CLI example prints Engineering. Accept Faculty of Engineering.
- **Why in scope:** W0 grader-contract example; same fact as G03 with different wording.

### G11 · Lv3 · given

- **Question:** How many tables are in Makerspace A?
- **Expected:** 11
- **Notes:** W2: taken from the published competition specification. Lab page also says eleven work tables, but the spec treats this as a visual extraction.
- **Why in scope:** Published spec Lv3 object-count; description schema field 2.
- **Failure mode:** described badly: 'several tables'

### G12 · Lv3 · given

- **Question:** What three words are on the wall behind the brainstorming area?
- **Expected:** HKU ENGINEERING INNOVATION
- **Notes:** W2 published spec. Copy exactly; do not translate or summarise.
- **Why in scope:** Published spec verbatim signage; schema field 3.
- **Failure mode:** paraphrase of the motto

### G13 · Lv4 · given

- **Question:** Which faculty runs the Innovation Wing, and who is its director?
- **Expected:** Faculty of Engineering; director name from indexed staff page or nameplate (not lab's Professor Amelia Reyes unless that is on the real site)
- **Notes:** W2 compound example. Current pages.json has faculty but no director name. Lab corpus director is teaching fiction.
- **Why in scope:** Lv4 decomposition: two subjects, one embedding otherwise lands between faculty and staff pages.
- **Failure mode:** compound embedding midpoint; answers only the first clause

### G14 · Lv4 · given

- **Question:** How many workshop posters are on the Innovation Academy website for 2025?
- **Expected:** 31
- **Notes:** W2 wording uses singular website; G08 uses websites. Keep both; grader may pick either.
- **Why in scope:** W2 counting lecture; same gold as G08, different surface form.

### G15 · Lv5 · given

- **Question:** What three words are on the wall behind the seating?
- **Expected:** HKU ENGINEERING INNOVATION
- **Notes:** Labs/lab4_description_prompt.ipynb TEST_QUESTIONS example. Same gold as G12, seating vs brainstorming area.
- **Why in scope:** Workshop-given visual/layout probe the lab tells teams to write.

### G16 · Lv5 · given

- **Question:** What is on the bench by the window?
- **Expected:** Electronics bench equipment (soldering stations, PSU, oscilloscope, hot-air rework) — confirm from the team's photo of Makerspace B.
- **Notes:** lab4 example. Lab text lists two soldering stations, a bench PSU, a two-channel oscilloscope, a hot air rework station.
- **Why in scope:** In-scope equipment + spatial relation (by the window).

### X01 · Lv1 · extra

- **Question:** 3D 打印也被称为什么？
- **Expected:** Additive manufacturing
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese stem of G01; grader is English but user asked Chinese tests.

### X02 · Lv1 · extra

- **Question:** 在 3D 打印里，FDM 代表什么？
- **Expected:** Fused deposition modelling
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese stem of G02.

### X03 · Lv1 · extra

- **Question:** Tam Wing Fan Innovation Wing 属于哪个学院？
- **Expected:** Faculty of Engineering
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese stem of G10/G03.

### X04 · Lv2 · extra

- **Question:** 激光切割机禁止使用哪两种材料？
- **Expected:** PVC and polycarbonate
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese stem of G05.

### X05 · Lv2 · extra

- **Question:** 2025-26 学年 Funding Scheme 第二轮截止日期是哪一天？
- **Expected:** 27 February 2026
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G04; ignore lab 20 Feb.

### X06 · Lv3 · extra

- **Question:** 2025 年 Pitch New Tech Ideas 的优胜队伍有哪些？
- **Expected:** Smartsocks, Digitio, Gingtrolley
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G06.

### X07 · Lv4 · extra

- **Question:** 中心一共运行多少台 3D 打印机？
- **Expected:** 7
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G07.

### X08 · Lv4 · extra

- **Question:** 2025 年 Innovation Academy 网站上有多少张 workshop 海报？
- **Expected:** 31
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G14.

### X09 · Lv5 · extra

- **Question:** 头脑风暴区后方墙上的三个词是什么？
- **Expected:** HKU ENGINEERING INNOVATION
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G12.

### X10 · Lv5 · extra

- **Question:** 在头脑风暴区后方的墙上有三个词。HKU、Engineering，以及……？
- **Expected:** Innovation
- **Notes:** Surface-form variant of an official/spec question; gold unchanged.
- **Why in scope:** Chinese of G09 fill-in.

### X11 · Lv1 · extra

- **Question:** What does the abbreviation FDM expand to?
- **Expected:** Fused deposition modelling
- **Notes:** Paraphrase of G02; retrieval/LLM must not invent Fused Deposition Modeling US spelling if gold is modelling.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X12 · Lv1 · extra

- **Question:** Is 3D printing a subtractive or additive process?
- **Expected:** Additive (additive manufacturing)
- **Notes:** Lv1 concept behind G01.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X13 · Lv1 · extra

- **Question:** 港大 Tam Wing Fan Innovation Wing 的英文全称是什么？
- **Expected:** Tam Wing Fan Innovation Wing
- **Notes:** Name exactness; W0/W2 subject of the contest.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X14 · Lv1 · extra

- **Question:** Which university houses the Tam Wing Fan Innovation Wing?
- **Expected:** The University of Hong Kong (HKU)
- **Notes:** pages.json heading text: Faculty of Engineering The University of Hong Kong.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X15 · Lv1 · extra

- **Question:** What academic fields does Inno Wing say it promotes interdisciplinary innovation in?
- **Expected:** Engineering and Technology
- **Notes:** Lv1/Lv2 about-page fact.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X16 · Lv1 · extra

- **Question:** Inno Wing 的教育目标 Educational Aim 强调把项目交给谁来主导？
- **Expected:** Students / undergraduates (entrusting and empowering students)
- **Notes:** About page educational aim.
- **Why in scope:** Lv1/easy site fact the prelim still scores.

### X17 · Lv2 · extra

- **Question:** What is Pitch New Tech Ideas according to Innovation Academy?
- **Expected:** A project pitching event for students to present ideas and recruit teammates and academic advisors to form student interest groups.
- **Notes:** pages.json heading Pitch New Tech Ideas. Contrast with G06 (winners are NOT in this paragraph).
- **Why in scope:** Lv2 programme text vs Lv3 image-only winners.

### X18 · Lv2 · extra

- **Question:** What three goals do Innovation Academy programmes capture?
- **Expected:** Inspire, Equip and Showcase
- **Notes:** pages.json Our Programmes & Activities.
- **Why in scope:** Lv2 buried list on the Academy site.

### X19 · Lv2 · extra

- **Question:** What does the Innovation Academy say it is a hub for?
- **Expected:** Attracting and cultivating talents: scholars, researchers, industry leaders and influencers; an accelerator for inspiration and implementation.
- **Notes:** pages.json About us.
- **Why in scope:** Lv2 about-text.

### X20 · Lv2 · extra

- **Question:** Name the four student interest groups listed on the Innovation Wing One page.
- **Expected:** Design, Build and Fly; Engineering and Archaeology; HKU Racing; HKU Robocon
- **Notes:** Headings on innowings.engg.hku.hk/innowing1/. Empty body text — titles themselves are the fact.
- **Why in scope:** Lv2/heading retrieval; related posters are Lv3.

### X21 · Lv2 · extra

- **Question:** Innovation Academy 的 Funding Scheme 用的是哪两个基金的名字？
- **Expected:** Tam Wing Fan Innovation Fund and Philomathia Foundation Innovation Fund
- **Notes:** pages.json Funding Scheme for projects / activities.
- **Why in scope:** Lv2 named funds on the real Academy page.

### X22 · Lv2 · extra

- **Question:** What medal did HKU iGEM win at the 2025 iGEM Competition?
- **Expected:** Gold Medal
- **Notes:** Student Achievements text AND image alt on innoacademy.engg.hku.hk.
- **Why in scope:** Lv2 if indexed from the achievements paragraph; also in image alt (Lv3 fallback).

### X23 · Lv2 · extra

- **Question:** Which project did the SRA team win the HKAE Pitch Competition with?
- **Expected:** ACTalyse: Adaptive Communication Training for Interdisciplinary Professionals
- **Notes:** Achievements paragraph / image alt.
- **Why in scope:** Lv2 long proper name; easy to truncate.

### X24 · Lv2 · extra

- **Question:** What result did HKU RAICOM Robotics achieve, in which category, and where/when was the national final?
- **Expected:** Third Class Honour in Treasure Hunter – Semi-Autonomous Mission; RAICOM National Final, August 2025, Hangzhou.
- **Notes:** Compound-looking but all in one achievements sentence — still Lv2 if retrieved; good routing test vs Lv4.
- **Why in scope:** Long fact; models drop category or city.

### X25 · Lv2 · extra

- **Question:** Which Student Interest Group was selected for the Hult Prize 2025 Incubator Programme?
- **Expected:** WeGoALGAE
- **Notes:** Achievements + image alt/caption.
- **Why in scope:** Lv2 named SIG.

### X26 · Lv2 · extra

- **Question:** Who was crowned champion at the HKAE Pitch Competition on Grand Challenge Engineering Topics for University Students 2024-25?
- **Expected:** Innogrow
- **Notes:** Alt: Innogrow crowned champion…
- **Why in scope:** Lv2/alt; year 2024-25 not 2025 Pitch New Tech.

### X27 · Lv2 · extra

- **Question:** What place did RoboMaster achieve at the RMUL Zhejiang Station competition?
- **Expected:** Fourth place
- **Notes:** Student Achievements / alt.
- **Why in scope:** Lv2 numeric result in text.

### X28 · Lv2 · extra

- **Question:** Engineering Inno Show 是什么活动、在什么时候举办？
- **Expected:** A showcase carnival at the end of every semester celebrating learning and creation; students demo projects and get feedback.
- **Notes:** pages.json Inno Show. Not Event Hall capacity (out of Lv5 collection).
- **Why in scope:** Lv2 programme text on the Academy site.

### X29 · Lv2 · extra

- **Question:** What is a Student Initiated Course at Innovation Academy?
- **Expected:** A student-run experiential activity to design, develop and teach a technology-related course under a Faculty Advisor; topics not covered in the formal curriculum.
- **Notes:** pages.json Student-initiated courses.
- **Why in scope:** Lv2.

### X30 · Lv2 · extra

- **Question:** What topics does Pitch New Tech Ideas list as example SIG areas?
- **Expected:** Robotics, artificial intelligence, electric automobiles and healthcare technologies
- **Notes:** Same Pitch paragraph as X17; list extraction.
- **Why in scope:** Lv2 list; incomplete list = 0.5.

### X31 · Lv2 · extra

- **Question:** Innovation Wing Tutor 团队用一句话怎么描述自己？
- **Expected:** Multidisciplinary Tutor Team – Broadest engineering skill coverage
- **Notes:** pages.json Innovation Wing Tutor. Verbatim of the heading text.
- **Why in scope:** Short site slogan; paraphrase may lose 'broadest'.

### X32 · Lv2 · extra

- **Question:** What intern skill areas does Student Development Projects mention?
- **Expected:** Artificial intelligence, computer vision, electronics, and robotics
- **Notes:** pages.json Student Development Projects.
- **Why in scope:** Lv2.

### X33 · Lv2 · extra

- **Question:** Which two materials may be cut on the laser cutter in the sample equipment page?
- **Expected:** Contest gold for banned materials is PVC and polycarbonate (G05). Permitted in the lab page: acrylic, plywood and cardboard.
- **Notes:** If the real site whitelist differs, use the real site. This extra tests permitted vs banned pairing.
- **Why in scope:** Equipment text retrieval; related to G05.

### X34 · Lv2 · extra

- **Question:** Funding Scheme 的钱可以花在什么上、不可以花在什么上？（若网页有清单）
- **Expected:** Lab gold: materials, components, consumables, equipment under $500; not travel, catering, salaries, software subscriptions. Confirm on the live funding page.
- **Notes:** Lab funding-scheme.txt. Real Philomathia/Tam Wing Fan scheme text may differ — retrieve don't memorise lab.
- **Why in scope:** Lv2 eligibility rules.

### X35 · Lv3 · extra

- **Question:** What exact text is on the sign above the door of Makerspace A?
- **Expected:** MAKERSPACE A
- **Notes:** W2 slide 14 Prompt B sample extraction.
- **Why in scope:** Verbatim signage; paraphrase of room name is not enough.
- **Failure mode:** C described badly

### X36 · Lv3 · extra

- **Question:** How many 3D printers stand along the north wall of Makerspace A?
- **Expected:** 4
- **Notes:** W2 slide 11 example description. Different from G07 total of 7.
- **Why in scope:** Count + spatial relation inside an image.
- **Failure mode:** confuses room total with wall count

### X37 · Lv3 · extra

- **Question:** What does the whiteboard in Makerspace A say about booking?
- **Expected:** Booking via portal
- **Notes:** W2 slide 11. Copy, don't summarise as 'book online'.
- **Why in scope:** Visible text field 3.

### X38 · Lv3 · extra

- **Question:** What material are the four-person tables in Makerspace A?
- **Expected:** Wooden / wooden tables
- **Notes:** W2 example: eleven wooden tables.
- **Why in scope:** Colour/material only where it identifies the object (schema field 5).

### X39 · Lv3 · extra

- **Question:** Makerspace A 里有多少张桌子？
- **Expected:** 11
- **Notes:** Chinese of G11.
- **Why in scope:** Published spec count in the user's language.

### X40 · Lv3 · extra

- **Question:** How many chairs are in Makerspace A in the workshop example extraction?
- **Expected:** Eleven chairs (W2 slide 14 Prompt B). Confirm on the team's photo — spec example used 11 chairs and 11 tables.
- **Notes:** Slide 14 lists four 3D printers, eleven chairs, two workbenches.
- **Why in scope:** Object counts; 'some chairs' fails.

### X41 · Lv3 · extra

- **Question:** How many workbenches does the W2 example description record in Makerspace A?
- **Expected:** Two workbenches
- **Notes:** W2 slide 14.
- **Why in scope:** Second count besides tables.

### X42 · Lv3 · extra

- **Question:** What is the title text on the Design, Build and Fly 2023 poster hosted on Innovation Wing?
- **Expected:** Read from the poster pixels (images.json has 01.-Design-Build-and-Fly-Team-2023-Poster-723x1024-1.png with empty alt).
- **Notes:** Empty alt → must describe/OCR. W2 tiling/small-print failure.
- **Why in scope:** Lv3 dense poster; never collected or small text lost after downscale.
- **Failure mode:** small print / no alt

### X43 · Lv3 · extra

- **Question:** Which Pitch New Tech Ideas 2025 winner was selected for the 8th HKTDC Start-up Express?
- **Expected:** Digitio (image alt writes Digitoe)
- **Notes:** images.json alt. Tests alt indexing without vision, and spelling vs G06 gold Digitio.
- **Why in scope:** W2: index alt text regardless.
- **Failure mode:** never collected; spelling

### X44 · Lv3 · extra

- **Question:** What does the Innovation Wing logo image contain (text or mark)?
- **Expected:** Whatever is visible on InnoWing-Logo.jpg — transcribe any wordmark exactly.
- **Notes:** images.json, empty alt. Logo is a classic 'never described' miss.
- **Why in scope:** Lv3 image with no alt.
- **Failure mode:** B never described

### X45 · Lv3 · extra

- **Question:** HKU Robocon 在 ABU Robocon 为香港取得了什么历史成绩？（以成就图/说明为准）
- **Expected:** Historic first championship representing Hong Kong (alt: clinches historic first championship).
- **Notes:** Image alt on innoacademy; also in Student Achievements text so may be Lv2 if that paragraph is indexed.
- **Why in scope:** Visual card + alt; if scraper skipped img, text paragraph may still save it.

### X46 · Lv3 · extra

- **Question:** What typo appears in the Robocon Hong Kong 2026 image alt text?
- **Expected:** cllinches (double l) in 'HKU Robocon cllinches back-to-back victory…'
- **Notes:** If the bot copies alt exactly it will reproduce the typo; if it 'fixes' it, retrieval still must find the chunk.
- **Why in scope:** Alt indexing; exact-copy vs silent correction.

### X47 · Lv3 · extra

- **Question:** Transcribe every word visible on the wall behind the brainstorming seating, in order.
- **Expected:** HKU ENGINEERING INNOVATION (write [unreadable] for any glyph you cannot see — W2 instruction)
- **Notes:** Same gold as G12; stresses order and no guessing.
- **Why in scope:** Verbatim + unreadable policy from W2 slide 12.
- **Failure mode:** invented words instead of [unreadable]

### X48 · Lv3 · extra

- **Question:** Makerspace A 北墙的 3D 打印机在桌子的哪一侧、对着什么？
- **Expected:** Along the north wall; spatial relation as in the team's photo (W2 example: printers along the north wall, tables in the room).
- **Notes:** Schema field 4. Do not accept 'equipment along the far wall'.
- **Why in scope:** Spatial relations the caption-style prompt drops.
- **Failure mode:** C generic caption

### X49 · Lv3 · extra

- **Question:** Copy the alt text of the AI workshop image on the Innovation Academy homepage.
- **Expected:** AI workshop - Build you ChatBot
- **Notes:** images.json alt, including the grammar error you.
- **Why in scope:** Alt already text; W2 says index it. Tests exact copy of a short line.

### X50 · Lv3 · extra

- **Question:** Describe only the visible text on the 2023 Design-Build-and-Fly poster, not the layout.
- **Expected:** OCR/transcription of the poster (second, text-only description pass — W2 slide 16).
- **Notes:** Advanced technique: two prompts per image, one objects, one text-only.
- **Why in scope:** Dense signage; vision paraphrases, OCR transcribes.

### X51 · Lv4 · extra

- **Question:** Which faculty runs the Tam Wing Fan Innovation Wing, and who is its director?
- **Expected:** Faculty of Engineering + director from staff/nameplate. W2 split example uses this longer name in sub-question 1.
- **Notes:** Slide 24 split wording. Keep G13 short form and this long form.
- **Why in scope:** Same compound skill; Tam Wing Fan full name vs Innovation Wing.

### X52 · Lv4 · extra

- **Question:** 哪个学院运营 Innovation Wing，主任是谁？
- **Expected:** 学院 Faculty of Engineering；主任需真站/铭牌。不要用 lab 的 Professor Amelia Reyes 除非真站如此。
- **Notes:** Chinese of G13.
- **Why in scope:** User-language compound question.

### X53 · Lv4 · extra

- **Question:** List each 3D printer model the Centre runs and the count per model, then the total.
- **Expected:** Lab split: 4× Prusa MK4, 2× Bambu X1C, 1× Formlabs Form 4, total 7. Confirm against the real equipment page/photos.
- **Notes:** W2: list evidence first then answer. Current answer.py strips to the first digit on 'how many' — this stem avoids that somewhat but still contains counts.
- **Why in scope:** Lv4 aggregate + evidence list.

### X54 · Lv4 · extra

- **Question:** How many FDM printers and how many resin printers does the Centre run?
- **Expected:** Lab: 6 FDM (4 Prusa + 2 Bambu) and 1 resin (Form 4). Total still 7.
- **Notes:** Comparison/filter inside the printer set.
- **Why in scope:** Lv4 filter then count; two numbers in one question.

### X55 · Lv4 · extra

- **Question:** Makerspace A 和 Makerspace B 的容量分别是多少人？哪个适合个人不预约进场？
- **Expected:** Lab: A 40, B 24; individuals use B drop-in desks. Verify on real venue pages/photos.
- **Notes:** Two rooms + a policy clause = decompose.
- **Why in scope:** Lv4 multi-subject.

### X56 · Lv4 · extra

- **Question:** How many of the homepage SIG names refer to student racing or robot competitions?
- **Expected:** At least HKU Racing and HKU Robocon (2). Design, Build and Fly is also a competition team — count 3 if the team includes DBF; say which rule you used.
- **Notes:** Answer is not written; must list SIGs then classify. Typical Lv4.
- **Why in scope:** Count after retrieving a set of headings.

### X57 · Lv4 · extra

- **Question:** Among the Student Achievements on the Innovation Academy homepage, how many distinct teams or projects are named?
- **Expected:** Count the named entities in that paragraph (HKU Engineering Team/Robocon, SRA/ACTalyse, iGEM, RAICOM Robotics, Digitoe, WeGoALGAE, Innogrow, RoboMaster) — about 8. List them then count.
- **Notes:** No chunk contains the integer. Metadata/list-then-count.
- **Why in scope:** Lv4 set count like the 31 posters.

### X58 · Lv4 · extra

- **Question:** Which achievements on the Academy site happened in 2025, and which in 2026?
- **Expected:** 2025: iGEM gold, RAICOM (Aug 2025 Hangzhou), Pitch New Tech Ideas / HKTDC, Hult Prize 2025, RMUL. 2026: Robocon Hong Kong 2026, ABU Robocon championship item dated 2026 in image URLs. List evidence by year.
- **Notes:** Needs year metadata or filtering; mixed years in one blob.
- **Why in scope:** Lv4 filter by year then list.

### X59 · Lv4 · extra

- **Question:** 同时回答：Inno Show 在每学期什么时候举行，以及 Pitch New Tech Ideas 用来组建什么？
- **Expected:** Inno Show: end of every semester. Pitch: form student interest groups (recruit teammates and advisors).
- **Notes:** Two programme pages; one embedding sits between them.
- **Why in scope:** Lv4 decompose two subjects.

### X60 · Lv4 · extra

- **Question:** How many images are currently recorded in submission_repo/data/images.json, and how many of those have non-empty alt text?
- **Expected:** 26 images, 11 with alt (inventory at the time this set was written). Re-count from the JSON if rebuilt.
- **Notes:** Not a contest gold — diagnostic count for Cause A. Still the same skill as poster counting.
- **Why in scope:** Counting over a stored image inventory; kNN cannot answer.

### X61 · Lv4 · extra

- **Question:** Compare Makerspace A booking rules with Makerspace B: who may book A, and what can you use in B without a booking?
- **Expected:** Lab: teams of three or more book A; B has six drop-in desks without booking. Confirm live.
- **Notes:** Comparison across two venue chunks.
- **Why in scope:** Lv4 comparison.

### X62 · Lv4 · extra

- **Question:** Does the Centre's 7 printers figure include the four along Makerspace A's north wall, or are those extra? Explain from evidence.
- **Expected:** Need both the total-7 chunk and the north-wall-4 image description. If photos show printers in A that are the same print-room bank, 7 is inclusive; if A has a separate row, totals change. List evidence; do not guess.
- **Notes:** Crosses G07 (Lv4 text/table) and X36 (Lv3 image). True synthesis.
- **Why in scope:** Lv4 assemble from image description + equipment text.

### X63 · Lv5 · extra

- **Question:** 站在头脑风暴区座位区，背后墙上三个英文词从左到右原文是什么？
- **Expected:** HKU ENGINEERING INNOVATION
- **Notes:** Must come from the team's own photo (Labs/images/Brainstorming aerial.JPG for practice).
- **Why in scope:** Lv5 in-scope venue signage; same gold as G12 but physical capture.

### X64 · Lv5 · extra

- **Question:** Where are the mobile whiteboards in the brainstorming area relative to the seating?
- **Expected:** Lab: four mobile whiteboards along the back wall; seating in front. Confirm from aerial photo.
- **Notes:** Schema field 4 layout.
- **Why in scope:** Physical layout; not the Event Hall.

### X65 · Lv5 · extra

- **Question:** How many mobile whiteboards are kept in the brainstorming area?
- **Expected:** Four (lab). Count from the photo, not from memory of the lab page if you are testing Lv5.
- **Notes:** If the bot answers from sample_corpus text it is cheating the Lv5 skill even if the number matches.
- **Why in scope:** Lv5 object count in an in-scope venue.

### X66 · Lv5 · extra

- **Question:** Makerspace B 靠窗的 electronics bench 上有哪些仪器、各几台？
- **Expected:** Lab: 2 soldering stations, 1 bench power supply, 1 two-channel oscilloscope, 1 hot air rework station. Photograph to confirm.
- **Notes:** In-scope equipment. Window spatial cue from G16.
- **Why in scope:** W2 equipment + G16.

### X67 · Lv5 · extra

- **Question:** What colour and material identify the sofas or seating in the brainstorming area in your photos?
- **Expected:** Whatever the photo shows (W2 example mentioned colourful cubic sofas / a large blue sign). Copy colours only if they identify the object.
- **Notes:** Schema field 5. Do not write 'modern furniture'.
- **Why in scope:** Physical colour/material identification.

### X68 · Lv5 · extra

- **Question:** What award names and team names are on the award board in the gallery outside the office?
- **Expected:** Only from photographs of the gallery board. Lab news page says winners are on that board and not listed in the article.
- **Notes:** W2 in-scope: gallery outside the office. Webpage is an index, not the answer.
- **Why in scope:** Lv5 gallery; cannot scrape.
- **Failure mode:** answered from news prose with no names

### X69 · Lv5 · extra

- **Question:** 办公室外走廊 gallery 里，当前奖项板/展示照片上能逐字读到哪些队名？
- **Expected:** Transcribe from gallery photos. Do not invent from Academy homepage achievements.
- **Notes:** Verbatim from physical posters in the gallery.
- **Why in scope:** Lv5 posters in the gallery zone.

### X70 · Lv5 · extra

- **Question:** On the building floor plan in the gallery, which rooms are labelled besides the makerspaces?
- **Expected:** Read labels off the photographed floor plan. Lab gallery-index.txt says a floor plan hangs there.
- **Notes:** Visible text on a physical exhibit.
- **Why in scope:** Gallery + verbatim labels.

### X71 · Lv5 · extra

- **Question:** Where are the tool lockers in Makerspace A, and how many banks/rows are visible?
- **Expected:** Lab: a bank of tool lockers along the east wall. Count banks from makerspace.JPG / Makerspace close up.JPG.
- **Notes:** In-scope venue + equipment storage, not the machine workshop.
- **Why in scope:** Spatial + count in Makerspace A.

### X72 · Lv5 · extra

- **Question:** Makerspace A 北墙大屏能用哪些接口连接笔记本？（若现场贴纸/铭牌有写）
- **Expected:** Lab page: HDMI or USB-C. Prefer sticker/label on the display if photographed.
- **Notes:** If only on the website, this drops to Lv2; if on a physical label, Lv5.
- **Why in scope:** Equipment labels in an in-scope room.

### X73 · Lv5 · extra

- **Question:** Copy any safety or booking notice posted on the door or wall of Makerspace A or B, word for word.
- **Expected:** Exact poster/door text from the team's zone photos. Use [unreadable] rather than guess.
- **Notes:** W2 verbatim policy for physical signs.
- **Why in scope:** Lv5 visible text in venues (not machine workshop).
- **Failure mode:** paraphrase → 0

### X74 · Lv5 · extra

- **Question:** How many work tables are visible in your Makerspace A photographs, and does that match eleven?
- **Expected:** Count from Labs/images/makerspace.JPG and close-up; gold if fully visible is 11 (spec).
- **Notes:** Self-written Lv5 question after first photo pass — W2 slide 29.
- **Why in scope:** Physical recount of the spec table question.

### X75 · Lv5 · extra

- **Question:** What is the seating capacity of the Event Hall, and which microphones does it have?
- **Expected:** Do not answer from Lv5 photos — Event Hall is OUT of collection scope (W2 slide 27). If a website page exists: lab says 180 seats, lectern mic + four radio mics.
- **Notes:** Negative-scope item. Collection kit forbids machine workshop and event hall.
- **Why in scope:** Tests the exclusion boundary the grader still might ask as Lv2 web text, never as a photo question.

### X76 · Lv5 · extra

- **Question:** Machine workshop / 金工车间的床身尺寸或设备型号是什么？
- **Expected:** Out of Lv5 collection scope (machine workshop excluded). Only answer if the official websites publish it (then it is Lv2).
- **Notes:** Laser cutter Trotec Speedy 400 1000x610mm is lab machine-room text — that room is excluded from physical capture.
- **Why in scope:** Exclusion pair with X75.

### X77 · Lv3 · extra

- **Question:** Describe this image of Makerspace A.
- **Expected:** A generic caption is a FAILED answer for scoring. The useful answer is the five-field extraction (location, counts, verbatim text, spatial, identifying colours).
- **Notes:** Anti-pattern from W2 slide 14 Prompt A. Included so teams see that this user phrasing yields zero on spec questions.
- **Why in scope:** Documents the failure mode the grader will not ask but your prompt must not emulate.
- **Failure mode:** Prompt A caption

### X78 · Lv1 · extra

- **Question:** Which faculty would you expect an engineering innovation centreto belong to?
- **Expected:** The Faculty of Engineering
- **Notes:** Exact typo from the command string inside dev_set.json (missing space before 'to'). Keep as a robustness extra, not a replacement for G03.
- **Why in scope:** The bundled command in dev_set.json literally has centreto; a brittle matcher could fail.

### X79 · Lv4 · extra

- **Question:** Name the director of the Innovation Wing, and which faculty runs it? (director first)
- **Expected:** Same two facts as G13, reversed order. Faculty of Engineering + director.
- **Notes:** Without labelled sub-question chunks the model often answers only the first part — here that would be the harder half.
- **Why in scope:** Lv4 clause order trap from W2 slide 24 note.
- **Failure mode:** answers only first clause

### X80 · Lv2 · extra

- **Question:** What is the Engineering Inno Show described as on the Innovation Wing site?
- **Expected:** Visit our Engineering Inno Show is a heading with empty body on innowing1; Academy page calls it a showcase carnival at end of semester.
- **Notes:** Empty heading vs full paragraph — retrieval must not stop at the empty Inno Wing section.
- **Why in scope:** Lv2 across both contest sites (scrape both).

### X81 · Lv1 · extra

- **Question:** FDM 3D 打印的中文里常说的熔融沉积，对应的英文全称是什么？
- **Expected:** Fused deposition modelling
- **Notes:** Still G02 gold.
- **Why in scope:** Lv1 bilingual.

### X82 · Lv2 · extra

- **Question:** What format can Innovation Academy Sharings take?
- **Expected:** Flexible: talks, one-on-one dialogue, or panel discussion, with guest speakers (entrepreneurs, industry partners, researchers, alumni).
- **Notes:** pages.json Sharing.
- **Why in scope:** Lv2.

### X83 · Lv2 · extra

- **Question:** What is the Hands-on workshop programme borrowed from, conceptually?
- **Expected:** The writer-in-residence concept, for exchange on advanced technologies / research from Faculty of Engineering projects.
- **Notes:** pages.json Hands-on workshop.
- **Why in scope:** Lv2 unusual phrasing good for retrieval tests.

### X84 · Lv2 · extra

- **Question:** Study Tour 带学生去看什么？
- **Expected:** Prestigious universities and cutting-edge companies; latest technology and robotics R&D.
- **Notes:** pages.json Study Tour.
- **Why in scope:** Lv2.

### X85 · Lv3 · extra

- **Question:** What three words appear behind the brainstorming area: copy them in ALL CAPS as on the wall.
- **Expected:** HKU ENGINEERING INNOVATION
- **Notes:** Case-sensitive copy. W2: paraphrased sign scores zero.
- **Why in scope:** Verbatim case.

### X86 · Lv4 · extra

- **Question:** How many workshop posters for 2025 are on the Innovation Academy site, and name one of them if your index stores titles.
- **Expected:** 31, plus any one indexed poster title. The integer is not written on the site.
- **Notes:** Count + example; needs full-set retrieval then listing.
- **Why in scope:** Lv4 count plus a retrieved instance.

### X87 · Lv5 · extra

- **Question:** In Makerspace B, where is the parts store / consumables cupboard relative to the door?
- **Expected:** Lab: small parts store in the cupboard by the door. Confirm photographically.
- **Notes:** In-scope venue, not machine workshop.
- **Why in scope:** Lv5 spatial equipment storage.

### X88 · Lv5 · extra

- **Question:** gallery 走廊是否在办公时间以外开放？现场指示牌怎么写？
- **Expected:** Lab gallery page: open whenever the building is open. Prefer the physical sign if present.
- **Notes:** Hours on a gallery sign = Lv5 verbatim; hours only on website = Lv2.
- **Why in scope:** Gallery in-scope.

### X89 · Lv4 · extra

- **Question:** Which faculty runs Inno Wing and how many 3D printers does the Centre run?
- **Expected:** Faculty of Engineering; 7 printers.
- **Notes:** Compound mixing Lv1/2 faculty with Lv4 count — routing should still split.
- **Why in scope:** Cross-level compound.

### X90 · Lv3 · extra

- **Question:** From the Makerspace close-up photo, what labels or stickers are readable on the equipment?
- **Expected:** Transcribe stickers from Labs/images/Makerspace close up.JPG (practice) or team photos.
- **Notes:** Close-up is where small-print / tiling matters.
- **Why in scope:** Lv3/Lv5 small text on equipment.

