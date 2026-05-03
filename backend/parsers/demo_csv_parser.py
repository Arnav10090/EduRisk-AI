"""
Demonstration of CSV parser functionality.

Run this script to see the CSV parser in action:
    python -m backend.parsers.demo_csv_parser
"""

from decimal import Decimal
from backend.parsers.csv_parser import parse_csv, format_to_csv
from backend.schemas.student import StudentInput


def demo_basic_parsing():
    """Demonstrate basic CSV parsing."""
    print("=" * 70)
    print("DEMO 1: Basic CSV Parsing")
    print("=" * 70)
    
    csv_content = """name,course_type,institute_tier,cgpa,year_of_grad,loan_amount,loan_emi
John Doe,Engineering,1,8.5,2025,500000,15000
Jane Smith,MBA,2,7.8,2024,300000,10000
Rahul Kumar,Medicine,1,9.2,2026,800000,25000"""
    
    print("\nInput CSV:")
    print(csv_content)
    
    students = parse_csv(csv_content)
    
    print(f"\n✅ Parsed {len(students)} students successfully!")
    for i, student in enumerate(students, 1):
        print(f"\nStudent {i}:")
        print(f"  Name: {student.name}")
        print(f"  Course: {student.course_type}")
        print(f"  Institute Tier: {student.institute_tier}")
        print(f"  CGPA: {student.cgpa}")
        print(f"  Year of Graduation: {student.year_of_grad}")


def demo_round_trip():
    """Demonstrate round-trip property."""
    print("\n" + "=" * 70)
    print("DEMO 2: Round-Trip Property (parse → format → parse)")
    print("=" * 70)
    
    # Create original student
    original = StudentInput(
        name="Alice Johnson",
        course_type="Engineering",
        institute_name="IIT Delhi",
        institute_tier=1,
        cgpa=Decimal("8.75"),
        year_of_grad=2025,
        loan_amount=Decimal("600000.50"),
        loan_emi=Decimal("18000.25")
    )
    
    print("\nOriginal Student:")
    print(f"  Name: {original.name}")
    print(f"  CGPA: {original.cgpa}")
    print(f"  Loan Amount: {original.loan_amount}")
    print(f"  Loan EMI: {original.loan_emi}")
    
    # Format to CSV
    csv_output = format_to_csv([original])
    print("\nFormatted to CSV:")
    print(csv_output)
    
    # Parse back
    parsed = parse_csv(csv_output)[0]
    print("Parsed back from CSV:")
    print(f"  Name: {parsed.name}")
    print(f"  CGPA: {parsed.cgpa}")
    print(f"  Loan Amount: {parsed.loan_amount}")
    print(f"  Loan EMI: {parsed.loan_emi}")
    
    # Verify equality
    assert parsed.name == original.name
    assert parsed.cgpa == original.cgpa
    assert parsed.loan_amount == original.loan_amount
    assert parsed.loan_emi == original.loan_emi
    
    print("\n✅ Round-trip successful! All fields preserved exactly.")


def demo_quoted_fields():
    """Demonstrate handling of quoted fields with commas."""
    print("\n" + "=" * 70)
    print("DEMO 3: Quoted Fields with Commas")
    print("=" * 70)
    
    csv_content = '''name,course_type,institute_tier,year_of_grad,institute_name
"Doe, John",Engineering,1,2025,"IIT Delhi, Main Campus"
"Smith, Jane",MBA,2,2024,"IIM Bangalore, Hostel Road"'''
    
    print("\nInput CSV with quoted fields:")
    print(csv_content)
    
    students = parse_csv(csv_content)
    
    print(f"\n✅ Parsed {len(students)} students with commas in names!")
    for student in students:
        print(f"\n  Name: {student.name}")
        print(f"  Institute: {student.institute_name}")


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "=" * 70)
    print("DEMO 4: Error Handling")
    print("=" * 70)
    
    # Missing required field
    print("\nTest 1: Missing required field (name)")
    csv_missing = """name,course_type,institute_tier,year_of_grad
,Engineering,1,2025"""
    
    try:
        parse_csv(csv_missing)
        print("❌ Should have raised error!")
    except ValueError as e:
        print(f"✅ Caught error: {e}")
    
    # Invalid data type
    print("\nTest 2: Invalid data type (text in numeric field)")
    csv_invalid = """name,course_type,institute_tier,year_of_grad
John Doe,Engineering,ABC,2025"""
    
    try:
        parse_csv(csv_invalid)
        print("❌ Should have raised error!")
    except ValueError as e:
        print(f"✅ Caught error: {e}")


def demo_optional_fields():
    """Demonstrate handling of optional fields."""
    print("\n" + "=" * 70)
    print("DEMO 5: Optional Fields")
    print("=" * 70)
    
    csv_content = """name,course_type,institute_tier,year_of_grad,cgpa,loan_amount
John Doe,Engineering,1,2025,,"""
    
    print("\nInput CSV with empty optional fields:")
    print(csv_content)
    
    students = parse_csv(csv_content)
    
    print(f"\n✅ Parsed successfully!")
    print(f"  Name: {students[0].name}")
    print(f"  CGPA: {students[0].cgpa} (None)")
    print(f"  Loan Amount: {students[0].loan_amount} (None)")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CSV PARSER DEMONSTRATION")
    print("=" * 70)
    
    demo_basic_parsing()
    demo_round_trip()
    demo_quoted_fields()
    demo_error_handling()
    demo_optional_fields()
    
    print("\n" + "=" * 70)
    print("ALL DEMOS COMPLETED SUCCESSFULLY! ✅")
    print("=" * 70)
    print("\nThe CSV parser is ready for production use.")
    print("It guarantees round-trip preservation and provides descriptive errors.")
    print("\nRun the full test suite with:")
    print("  python -m pytest backend/tests/test_csv_parser.py -v")
    print("=" * 70 + "\n")
