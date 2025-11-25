# CIB_Data-Analyst
Data Analyst team for CIB (นักวิเคราะห์ข้อมูลของตำรวจสอบสวนกลาง)

## 🧠 ระบบวิเคราะห์ข้อมูล TPO พร้อมดาวน์โหลด PDF
แอป Streamlit ที่พัฒนาในโปรเจ็กต์นี้ช่วยอัปโหลดภาพสถิติ TPO, แยกข้อมูลด้วย Gemini Vision, สร้างกราฟ Plotly และดาวน์โหลดรายงาน PDF อัตโนมัติ

### 🔄 Workflow การประมวลผล
```
[รูปภาพสถิติหลายไฟล์]
        ↓
[อัปโหลดผ่าน Web UI ของ Streamlit]
        ↓
[Gemini Vision API แยกข้อมูลเป็น JSON]
        ↓
[วิเคราะห์แนวโน้ม + จัดอันดับคดี]
        ↓
[สร้างกราฟ Plotly/Kaleido]
        ↓
[รวมผลเป็น HTML + ReportLab]
        ↓
[ดาวน์โหลดรายงาน PDF]
```

### 🏛️ สถาปัตยกรรมที่รองรับ
- **Option 1 – Streamlit (ภายในรีโปนี้)**
  - Frontend + Backend รวมอยู่ใน Streamlit
  - เรียก `google-generativeai` เพื่อใช้ Gemini Vision + Text
  - กราฟ Interactive ด้วย Plotly / PDF ผ่าน ReportLab + Kaleido
- **Option 2 – Pure Web App (HTML + JS)**
  - ใช้ Chart.js + jsPDF/html2canvas (มีตัวอย่างโค้ดในคำอธิบาย)
  - เรียก Gemini API ผ่าน REST จากเบราว์เซอร์ (ต้องระวังการจัดเก็บ API Key)

## ⚙️ การติดตั้ง
1. ติดตั้ง Python 3.10+ และสร้าง virtual environment  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. ติดตั้ง dependencies  
   ```bash
   pip install -r requirements.txt
   ```
3. คัดลอกไฟล์ตัวอย่าง secrets แล้วใส่ API Key  
   ```bash
   cp .streamlit/secrets.example.toml .streamlit/secrets.toml
   ```
   จากนั้นแก้ค่า `GEMINI_API_KEY`
4. ดาวน์โหลดฟอนต์ `THSarabunNew.ttf` (Google Fonts) แล้ววางไว้ที่ root เพื่อให้ PDF แสดงภาษาไทยสมบูรณ์

## ▶️ การใช้งานแอป
```bash
streamlit run app.py
```
- อัปโหลดภาพกราฟ/ตารางสถิติจากระบบ TPO (รองรับหลายไฟล์)
- กดปุ่ม **“เริ่มวิเคราะห์”** เพื่อเรียก Gemini Vision
- ดูผลลัพธ์: ตาราง, เมตริก, กราฟ Interactive
- ดาวน์โหลดรายงาน PDF พร้อมกราฟด้วยปุ่ม **“ดาวน์โหลดรายงาน PDF”**
- หากยังไม่มี API Key สามารถเปิด toggle “ใช้ข้อมูลตัวอย่าง” เพื่อทดลองฟีเจอร์ทั้งหมด

## 🗂️ โครงสร้างไฟล์ที่เกี่ยวข้อง
```
app.py                       # โค้ดหลักของ Streamlit App
requirements.txt             # รายการ dependencies
.streamlit/secrets.example.toml  # ตัวอย่างไฟล์ตั้งค่า API Key
README.md                    # เอกสารอธิบายโปรเจ็กต์
```

## 📋 ฟีเจอร์สำคัญ
- อัปโหลดภาพหลายไฟล์พร้อมกัน พร้อมตัวอย่างแสดงทันที
- วิเคราะห์ข้อมูลด้วย Prompt เฉพาะทาง + Gemini Vision API
- สรุปแนวโน้มเปรียบเทียบรายสัปดาห์, Top 5 คดีทั้งตามจำนวนและความเสียหาย
- กราฟ Plotly 3 ประเภท + Bar Horizontal สำหรับความเสียหายเฉลี่ย
- ดาวน์โหลด PDF ผ่าน ReportLab โดยฝังกราฟที่เรนเดอร์ผ่าน Kaleido
- รองรับภาษาไทยครบถ้วนทั้ง UI และรายงาน

## 🚨 การแก้ปัญหาที่พบบ่อย
- **Streamlit แจ้งว่าไม่พบ GEMINI_API_KEY**  
  ตรวจสอบไฟล์ `.streamlit/secrets.toml` หรือ environment variable
- **สร้าง PDF แล้วพบฟอนต์เพี้ยน**  
  ยืนยันว่ามีไฟล์ `THSarabunNew.ttf` ใน root หรือแก้ชื่อฟอนต์ใน `app.py`
- **คอลข้อมูลไม่ครบจากรูปภาพ**  
  ใช้รูปความละเอียดสูง พยายามครอบเฉพาะกราฟ/ตาราง และเพิ่มแสงสว่าง

## 📚 หัวข้ออบรม Data Analyst (อ้างอิงหลักสูตรเดิม)
1. Spreadsheets (Google Sheets)  
2. SQL  
3. R Programming  
4. Data Transformation  
5. Data Visualization  
6. Python Programming  
7. ML / Generative AI  
8. Prompt Engineering  
9. GitHub  

## 📷 Image
![Data Analyst](https://jessup.edu/wp-content/uploads/2024/01/Is-Data-Analyst-a-Stressful-Job.jpg)

## 📮 Contact
ติดต่อได้ที่ wirachan52@gmail.com

