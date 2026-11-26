"""
Generator for Krishi Sakhi starter agriculture PDF knowledge base.
Produces clean, uncorrupted, standard-compliant PDF manuals for pest control, fertilizers, and government schemes.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_DIR = os.path.join(BASE_DIR, "data", "knowledge_base")

def create_dirs():
    for sub in ["pest_control", "fertilizers", "schemes"]:
        os.makedirs(os.path.join(KB_DIR, sub), exist_ok=True)

def build_pdf(filepath, title, subtitle, sections):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1b4332'),
        spaceAfter=6
    )
    
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#40916c'),
        spaceAfter=14
    )
    
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#2d6a4f'),
        spaceBefore=10,
        spaceAfter=5
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1b261e'),
        spaceAfter=8
    )

    story = [
        Paragraph(title, title_style),
        Paragraph(subtitle, sub_style),
        Spacer(1, 8)
    ]

    for heading, paragraphs in sections:
        story.append(Paragraph(heading, h2_style))
        for p in paragraphs:
            story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    print(f"Generated clean PDF: {filepath}")

def generate_all():
    create_dirs()

    # 1. Pest Control Guide
    pest_path = os.path.join(KB_DIR, "pest_control", "soybean_cotton_pest_guide.pdf")
    pest_sections = [
        (
            "1. Soybean Major Pest Management (Soybean Kid Niyantran Sallaha)",
            [
                "<b>Armyworm and Leaf-eating Caterpillar (Lashkari Aali va Pane Khanari Aali):</b> Symptoms include circular holes in leaves, skeletonized leaf tissue, and visible caterpillars feeding during early mornings or late evenings.",
                "<b>Biological and Mechanical Control (Jaivik Upay):</b> Install 5 pheromone traps (Kamgandh Sapale) per acre at early vegetative stage. Spray 5% Neem Seed Kernel Extract (NSKE / Nimboli Ark at 50 ml per 10 liters of water) to deter egg laying and young larval growth.",
                "<b>Chemical Control (Rasayanik Favarni):</b> When larval count exceeds Economic Threshold Level (ETL of 2 larvae per meter row), spray <b>Emamectin Benzoate 5% SG</b> at 4 grams per 10 liters of water OR <b>Chlorantraniliprole 18.5% SC</b> (Coragen) at 3 ml per 10 liters of water. Always spray during early morning or late afternoon."
            ]
        ),
        (
            "2. Girdle Beetle and Stem Fly in Soybean (Chakati Bhunga va Khodmashi)",
            [
                "<b>Symptoms:</b> Ring-like incisions on stems or petioles causing top leaves to droop, wither, and die. Stem hollows out upon split.",
                "<b>Management:</b> Collect and destroy affected plant parts. Spray <b>Thiamethoxam 12.6% + Lambda-cyhalothrin 9.5% ZC</b> at 3 ml per 10 liters of water."
            ]
        ),
        (
            "3. Cotton Pink Bollworm Management (Kapas Gulabi Bond Aali)",
            [
                "<b>Symptoms:</b> Rosetted flowers (Dom Kali), premature boll opening, stained lint, and larval entry holes plugged with excreta inside the boll.",
                "<b>Monitoring and Mass Trapping:</b> Install 8 to 10 pheromone traps per acre starting 45 days after sowing. Inspect 20 green bolls per acre every week.",
                "<b>Recommended Spray Schedule:</b> For early larval control, spray <b>Profenofos 50% EC</b> at 30 ml per 10 liters of water OR <b>Spinetoram 11.7% SC</b> at 8.5 ml per 10 liters of water. Strictly avoid monocrotophos."
            ]
        )
    ]
    build_pdf(
        pest_path,
        "ICAR-KVK Soybean and Cotton Pest Management Advisory 2024",
        "Authoritative Field Recommendations for Maharashtra and Central India Agriculture",
        pest_sections
    )

    # 2. Fertilizer Guide
    fert_path = os.path.join(KB_DIR, "fertilizers", "fertilizer_recommendations_guide.pdf")
    fert_sections = [
        (
            "1. Balanced NPK Dosage for Field Crops (Santulit Khat Vyavasthapan)",
            [
                "<b>Soybean (Soyabean):</b> Recommended NPK dose is 20:60:40 kg per hectare (or 8:24:16 kg per acre). Apply full dose at the time of sowing. Avoid excessive chemical nitrogen as soybean fixes atmospheric nitrogen through root nodules.",
                "<b>Cotton (Kapas - Bt Cotton):</b> Recommended NPK dose is 120:60:60 kg per hectare for rainfed, and 150:75:75 kg/ha for irrigated fields. Apply 20% Nitrogen with full Phosphorus and Potash at sowing. Top dress remaining Nitrogen in two split doses at square formation (40 days) and flowering (60 days).",
                "<b>Sugarcane (Oos):</b> Recommended NPK dose is 250:115:115 kg per hectare applied in 4 split doses: basal at planting, 6 to 8 weeks, 12 to 14 weeks, and final earthing up (Mothi Bandhani)."
            ]
        ),
        (
            "2. Micronutrient Management and Soil Health (Sukshma Annadravye va Mati Arogya)",
            [
                "<b>Zinc Deficiency (Zinc Kamtart):</b> Very common in black cotton soils, showing yellowing between leaf veins in young leaves. Apply Zinc Sulfate 21% at 10 to 15 kg per acre to the soil once every 2 years, OR foliar spray 0.5% (50 grams in 10 liters water).",
                "<b>Boron Application:</b> Essential for cotton boll retention and soybean pod filling. Foliar spray 20% Solubor at 1.5 grams per liter at flowering stage.",
                "<b>Organic Carbon Enhancement:</b> Incorporate 2 to 3 tonnes of well-rotted FYM (Shenkhat) or vermicompost per acre before pre-monsoon harrowing to boost soil moisture retention."
            ]
        )
    ]
    build_pdf(
        fert_path,
        "Agricultural University Soil and Fertilizer Advisory Guide 2024",
        "Scientific NPK Ratios, Micronutrients and Soil Nutrition Management Guidelines",
        fert_sections
    )

    # 3. Government Schemes Guide
    scheme_path = os.path.join(KB_DIR, "schemes", "pm_kisan_and_govt_schemes_guide.pdf")
    scheme_sections = [
        (
            "1. PM-KISAN Samman Nidhi Yojana (PM-Kisan Sanman Nidhi)",
            [
                "<b>Scheme Overview:</b> Under the PM-KISAN scheme, eligible small and marginal farmer families receive financial assistance of Rs. 6,000 per year directly transferred to active bank accounts via DBT in three equal 4-monthly installments of Rs. 2,000 each.",
                "<b>Mandatory Eligibility Criteria:</b> 1) Farmer must have land records seeded and verified in the state revenue portal (Bhumi Abhilekh). 2) Completed biometric or OTP-based e-KYC. 3) Bank account linked with Aadhaar and enabled for NPCI/Aadhaar Payment Bridge (Aadhaar Seeding).",
                "<b>Exclusions:</b> Institutional landholders, serving or retired government employees, income tax payees, and constitutional post holders are excluded."
            ]
        ),
        (
            "2. Namo Shetkari Mahasanman Nidhi Yojana (Maharashtra State Scheme)",
            [
                "<b>State Scheme Benefit:</b> The Government of Maharashtra provides an additional financial assistance of Rs. 6,000 per year to PM-KISAN beneficiaries in the state, bringing total annual farmer assistance to Rs. 12,000.",
                "<b>Disbursement Schedule:</b> Released in three installments of Rs. 2,000 each in coordination with central PM-KISAN installments."
            ]
        ),
        (
            "3. Pradhan Mantri Fasal Bima Yojana - PMFBY (Pik Vima Yojana)",
            [
                "<b>Maharashtra Special Feature:</b> Farmers can enroll their notified crops in PMFBY by paying a token premium of only Rs. 1, with the remainder subsidized by state and central governments.",
                "<b>Critical 72-Hour Intimation Rule:</b> In case of localized calamities (inundation, cloudburst, hailstorm, pest outbreak), the farmer must submit an intimation claim within 72 hours via the Crop Insurance App or toll-free number 14447 to be eligible for survey and compensation."
            ]
        )
    ]
    build_pdf(
        scheme_path,
        "Government Farmer Welfare Schemes and Subsidies Handbook 2024",
        "Official Rules, Eligibility, e-KYC Procedures and Crop Insurance Guidelines",
        scheme_sections
    )

if __name__ == "__main__":
    generate_all()
