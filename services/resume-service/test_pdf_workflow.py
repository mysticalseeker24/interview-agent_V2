#!/usr/bin/env python3
"""
Test script for the PDF resume processing workflow.
Tests: data/ → text_files/ → output/
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.resume_processor import ResumeProcessor


def test_pdf_workflow():
    """Test the complete PDF processing workflow."""
    print("🚀 TESTING PDF RESUME PROCESSING WORKFLOW")
    print("=" * 80)
    
    # Initialize processor
    processor = ResumeProcessor(use_llm=False)
    
    print("📊 Pipeline Configuration:")
    info = processor.get_pipeline_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 80)
    print("📁 DIRECTORY STRUCTURE:")
    
    # Check directories
    data_dir = Path("data")
    test_files_dir = data_dir / "test_files"
    output_dir = data_dir / "output"
    
    print(f"   📂 Data directory: {data_dir.absolute()}")
    print(f"   📂 Test files directory: {test_files_dir.absolute()}")
    print(f"   📂 Output directory: {output_dir.absolute()}")
    
    # Find PDF files in data directory
    pdf_files = list(data_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("\n❌ No PDF files found in data directory!")
        print(f"   Please place a PDF resume in: {data_dir.absolute()}")
        return
    
    print(f"\n📄 Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"   📝 {pdf_file.name}")
    
    print("\n" + "=" * 80)
    print("🔄 PROCESSING PDF RESUME")
    print("=" * 80)
    
    # Process the first PDF file
    pdf_file = pdf_files[0]
    print(f"🎯 Processing: {pdf_file.name}")
    
    # Process the resume
    result = processor.process_resume(str(pdf_file))
    
    print("\n📈 PROCESSING RESULTS:")
    print(f"   ✅ Success: {result.success}")
    
    if result.success:
        print(f"   ⏱️ Processing Time: {result.processing_time:.3f}s")
        print(f"   🏗️ Stages Completed: {', '.join(result.stages_completed)}")
        
        if result.text_file_path:
            print(f"   📄 Text File: {result.text_file_path}")
            # Check if text file exists
            if Path(result.text_file_path).exists():
                text_size = Path(result.text_file_path).stat().st_size
                print(f"      ✅ Text file created ({text_size} bytes)")
            else:
                print(f"      ❌ Text file not found!")
        
        if result.json_file_path:
            print(f"   📋 JSON File: {result.json_file_path}")
            # Check if JSON file exists
            if Path(result.json_file_path).exists():
                json_size = Path(result.json_file_path).stat().st_size
                print(f"      ✅ JSON file created ({json_size} bytes)")
            else:
                print(f"      ❌ JSON file not found!")
        
        if result.data:
            print(f"\n📊 EXTRACTED DATA OVERVIEW:")
            print(f"   📝 Text Length: {result.data.raw_text_length:,} characters")
            print(f"   🎯 Confidence: {result.data.parsing_confidence:.2%}")
            print(f"   🏷️ Sections Detected: {', '.join(result.data.sections_detected)}")
            print(f"   🎭 Domains: {', '.join(result.data.domains)}")
            
            print(f"\n👤 CONTACT INFORMATION:")
            contact = result.data.contact
            print(f"   Name: {contact.name or 'N/A'}")
            print(f"   Email: {contact.email or 'N/A'}")
            print(f"   Phone: {contact.phone or 'N/A'}")
            print(f"   LinkedIn: {contact.linkedin or 'N/A'}")
            print(f"   GitHub: {contact.github or 'N/A'}")
            
            print(f"\n💼 EXPERIENCE ({len(result.data.experience)} entries):")
            for i, exp in enumerate(result.data.experience[:3], 1):  # Show first 3
                print(f"   {i}. {exp.position or 'Unknown Position'} at {exp.company or 'Unknown Company'}")
                if exp.start_date or exp.end_date:
                    print(f"      📅 {exp.start_date or 'N/A'} → {exp.end_date or 'N/A'}")
                print(f"      🏆 {len(exp.bullets)} achievements, {len(exp.metrics)} metrics")
            
            print(f"\n🛠️ SKILLS ({len(result.data.skills)} categories):")
            for skill_cat in result.data.skills[:5]:  # Show first 5 categories
                print(f"   {skill_cat.category}: {', '.join(skill_cat.skills[:5])}{'...' if len(skill_cat.skills) > 5 else ''}")
            
            print(f"\n🎓 EDUCATION ({len(result.data.education)} entries):")
            for edu in result.data.education:
                print(f"   📜 {edu.degree or 'Unknown Degree'} @ {edu.institution or 'Unknown Institution'}")
        
    else:
        print(f"   ❌ Error: {result.error_message}")
    
    print("\n" + "=" * 80)
    print("📂 CHECKING OUTPUT FILES")
    print("=" * 80)
    
    # List files in test_files directory
    txt_files = list(test_files_dir.glob("*.txt"))
    print(f"\n📄 Text files in {test_files_dir}:")
    if txt_files:
        for txt_file in txt_files:
            size = txt_file.stat().st_size
            print(f"   📝 {txt_file.name} ({size} bytes)")
    else:
        print("   (No text files found)")
    
    # List files in output directory
    json_files = list(output_dir.glob("*.json"))
    print(f"\n📋 JSON files in {output_dir}:")
    if json_files:
        for json_file in json_files:
            size = json_file.stat().st_size
            print(f"   📊 {json_file.name} ({size} bytes)")
            
            # Show a sample of the JSON
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"      Contact Name: {data.get('contact', {}).get('name', 'N/A')}")
                print(f"      Confidence: {data.get('parsing_confidence', 0):.2%}")
            except Exception as e:
                print(f"      ❌ Error reading JSON: {e}")
    else:
        print("   (No JSON files found)")
    
    print("\n" + "=" * 80)
    print("✅ PDF WORKFLOW TEST COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    test_pdf_workflow()
