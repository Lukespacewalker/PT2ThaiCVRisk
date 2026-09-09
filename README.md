# Thai CV Risk Score Dashboard - กองรักษาความปลอดภัย 2569

ระบบประเมินและแดชบอร์ดวิเคราะห์ความเสี่ยงโรคหัวใจและหลอดเลือด (Thai CV Risk Score: Ramathibodi / EGAT) ของเจ้าหน้าที่รักษาความปลอดภัย ประจำปี 2569 พัฒนาด้วย **Astro**, **Plotly.js**, และ **Mid-Century Modern Retro Theme** (สไตล์เดียวกับ PTT ASCVD Dashboard) รองรับการนำขึ้น **Cloudflare Pages** ทันที

---

## 🌟 จุดเด่นของระบบ (Key Features)
1. **การคำนวณ Thai CV Risk Score (Ramathibodi / EGAT Model)**:
   - ใช้ค่าทางคลินิก: อายุ, เพศ (ชาย), ความดัน Systolic (SBP), ระดับน้ำตาลในเลือดสะสม/FBS ($\ge 126$ mg/dL), และโคเลสเตอรอลรวม
   - ค่าตั้งต้นการสูบบุหรี่: กำหนดเป็น **ไม่สูบ (0)** สำหรับทุกคนตามคำสั่ง (อยู่ระหว่างรอข้อมูลสำรวจเพิ่มเติม)
   - โหมดจำลองประชากร (Simulated Mode) และโหมดสมมติว่าสูบ (What-if Mode) เพื่อวิเคราะห์ผลกระทบเมื่อมีการสูบบุหรี่
2. **การจัดระดับความเสี่ยงตามมาตรฐาน สธ. / รามาธิบดี**:
   - **เสี่ยงต่ำ (<10%)**: สีเขียว
   - **เสี่ยงปานกลาง (10–19.9%)**: สีเหลือง
   - **เสี่ยงสูง (20–29.9%)**: สีส้ม
   - **เสี่ยงสูงมาก ($\ge 30\%$)**: สีแดง
3. **การแสดงผลเชิงสถิติและการแพทย์อาชีวอนามัย**:
   - กราฟสัดส่วนระดับความเสี่ยง (Bar / Donut Chart)
   - กราฟ Scatter Plot แสดงความสัมพันธ์ระหว่าง อายุ, SBP และคะแนนความเสี่ยง
   - Box Plot แสดงการกระจายตัวของความเสี่ยงตามช่วงอายุ (<40, 40-49, 50-59 ปี)
   - สรุปความชุกของโรคร่วม: ภาวะเบาหวาน, ความดันโลหิตสูง, ไขมันในเลือดสูง, BMI เกินเกณฑ์
4. **ตารางข้อมูลรายบุคคลพร้อมการค้นหาและจัดเรียง**:
   - ค้นหาด้วยชื่อ หรือ ลำดับ
   - คลิกหัวตารางเพื่อเรียงลำดับ (Sorting)
5. **ระบบประเมินตนเอง (`/calculator`)**:
   - หน้ากรอกข้อมูลสุขภาพส่วนบุคคลแบบ Real-time พร้อมแถบวัดระดับความเสี่ยง (Risk Meter)
   - การวิเคราะห์ What-If เปรียบเทียบหากเลิกบุหรี่หรือควบคุมความดัน/ไขมัน
6. **รองรับ 2 ภาษา**: สลับภาษาไทย (TH) และภาษาอังกฤษ (EN) ได้ทันที

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)
```text
PT2Extractor/
├── data/                                 # ไฟล์ข้อมูลและสคริปต์ประมวลผล
│   ├── ตรวจสุขภาพ รปภ. ปี 2569.pdf         # เอกสารผลตรวจสุขภาพต้นฉบับ
│   ├── ตรวจสุขภาพ_รปภ_ปี2569_extracted.xlsx# ข้อมูลที่สกัดได้ (74 ราย)
│   ├── generate_thai_cv_data.py          # สคริปต์คำนวณ Thai CV Risk และสร้าง JSON
│   └── extraction_scripts/               # สคริปต์การสกัดข้อมูลและทดสอบเดิม
├── public/
│   └── favicon.svg                       # ไอคอน Favicon
├── src/
│   ├── data/
│   │   └── thai_cv_data.json             # ข้อมูลผลลัพธ์พร้อมใช้งานในเว็บ
│   ├── pages/
│   │   ├── index.astro                   # แดชบอร์ดหลัก
│   │   └── calculator.astro              # เครื่องคำนวณประเมินตนเอง
│   └── styles/
│       └── global.css                    # สไตล์ Mid-Century Modern Theme
├── dist/                                 # Static build output สำหรับ Cloudflare Pages
├── package.json
├── astro.config.mjs
└── tsconfig.json
```

---

## 🚀 การติดตั้งและรันในเครื่อง (Local Development)

### 1. ติดตั้ง Dependencies
```bash
bun install
# หรือ
npm install
```

### 2. รัน Local Development Server
```bash
bun run dev
# หรือ
npm run dev
```
เปิดเบราว์เซอร์ไปที่ `http://localhost:4321`

### 3. รันสคริปต์อัปเดตข้อมูล (หากมีการแก้ไข Excel)
```bash
.\.venv\Scripts\python.exe data/generate_thai_cv_data.py
```

---

## ☁️ วิธีการนำขึ้น Cloudflare Pages (Deploy to Cloudflare Pages)

### วิธีที่ 1: ผ่าน Git Repository (แนะนำ)
1. Push โค้ดนี้ขึ้น GitHub หรือ GitLab
2. ไปที่ [Cloudflare Dashboard](https://dash.cloudflare.com/) > **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**
3. เลือก Repository นี้
4. ตั้งค่า Build settings ดังนี้:
   - **Framework preset**: `Astro`
   - **Build command**: `bun run build` หรือ `npm run build`
   - **Build output directory**: `dist`
5. กด **Save and Deploy** ระบบจะ build และเผยแพร่เว็บไซต์ให้ทันที

### วิธีที่ 2: Direct Upload (ลากโฟลเดอร์ขึ้นโดยตรง)
1. รันคำสั่งคอมไพล์โปรเจกต์:
   ```bash
   bun run build
   # หรือ
   npm run build
   ```
2. โฟลเดอร์ `./dist` จะถูกสร้างขึ้นมา
3. ใน Cloudflare Pages เลือก **Upload Assets** แล้วลากไฟล์/โฟลเดอร์ทั้งหมดข้างใน `./dist` ขึ้นไปได้ทันที
