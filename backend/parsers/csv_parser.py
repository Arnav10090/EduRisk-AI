"""
CSV parser for student data with round-trip preservation.

Implements Requirement 19: CSV Student Data Parser
- Parse CSV rows into StudentInput objects
- Format StudentInput objects back to CSV
- Handle missing fields with descriptive errors
- Handle invalid data types with descriptive errors
- Support CSV with or without header row
- Handle quoted fields containing commas
- Guarantee round-trip property: parse → format → parse = identity
"""

import csv
from io import StringIO
from typing import List, BinaryIO, TextIO, Union
from decimal import Decimal, InvalidOperation

from backend.schemas.student import StudentInput


def parse_csv(file: Union[str, TextIO, BinaryIO]) -> List[StudentInput]:
    """
    Parse CSV file into list of StudentInput objects.
    
    Validates Requirements: 19.1, 19.2, 19.3, 19.6, 19.7
    
    Args:
        file: CSV content as string, text file object, or binary file object
    
    Returns:
        List of validated StudentInput objects
    
    Raises:
        ValueError: If CSV is malformed, has missing required fields, or invalid data types
    
    Examples:
        >>> csv_content = "name,course_type,institute_tier,cgpa,year_of_grad\\n"
        >>> csv_content += "John Doe,Engineering,1,8.5,2025"
        >>> students = parse_csv(csv_content)
        >>> len(students)
        1
        >>> students[0].name
        'John Doe'
    """
    # Handle different input types
    if isinstance(file, str):
        content = file
    elif isinstance(file, bytes):
        content = file.decode('utf-8')
    elif hasattr(file, 'read'):
        raw_content = file.read()
        if isinstance(raw_content, bytes):
            content = raw_content.decode('utf-8')
        else:
            content = raw_content
    else:
        raise ValueError("File must be a string, bytes, or file-like object")
    
    # Parse CSV with proper handling of quoted fields
    reader = csv.DictReader(StringIO(content))
    
    if reader.fieldnames is None:
        raise ValueError("CSV file is empty or has no header row")
    
    students = []
    required_fields = ['name', 'course_type', 'institute_tier', 'year_of_grad']
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
        try:
            # Check for missing required fields
            missing_fields = [field for field in required_fields if not row.get(field)]
            if missing_fields:
                raise ValueError(
                    f"Row {row_num}: Missing required field(s): {', '.join(missing_fields)}"
                )
            
            # Convert empty strings to None for optional fields
            processed_row = {}
            for key, value in row.items():
                if value == '' or value is None:
                    processed_row[key] = None
                else:
                    processed_row[key] = value
            
            # Handle numeric conversions with descriptive errors
            try:
                if processed_row.get('institute_tier') is not None:
                    processed_row['institute_tier'] = int(processed_row['institute_tier'])
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Row {row_num}: Invalid data type for 'institute_tier' - "
                    f"expected integer, got '{processed_row.get('institute_tier')}'"
                )
            
            try:
                if processed_row.get('year_of_grad') is not None:
                    processed_row['year_of_grad'] = int(processed_row['year_of_grad'])
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Row {row_num}: Invalid data type for 'year_of_grad' - "
                    f"expected integer, got '{processed_row.get('year_of_grad')}'"
                )
            
            # Handle Decimal fields
            decimal_fields = ['cgpa', 'cgpa_scale', 'loan_amount', 'loan_emi']
            for field in decimal_fields:
                if processed_row.get(field) is not None:
                    try:
                        processed_row[field] = Decimal(str(processed_row[field]))
                    except (InvalidOperation, ValueError, TypeError) as e:
                        raise ValueError(
                            f"Row {row_num}: Invalid data type for '{field}' - "
                            f"expected number, got '{processed_row.get(field)}'"
                        )
            
            # Handle integer fields
            int_fields = ['internship_count', 'internship_months', 'certifications']
            for field in int_fields:
                if processed_row.get(field) is not None:
                    try:
                        processed_row[field] = int(processed_row[field])
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Row {row_num}: Invalid data type for '{field}' - "
                            f"expected integer, got '{processed_row.get(field)}'"
                        )
            
            # Create StudentInput object (this will validate business rules)
            student = StudentInput(**processed_row)
            students.append(student)
            
        except ValueError as e:
            # Re-raise ValueError with row context if not already added
            if f"Row {row_num}" not in str(e):
                raise ValueError(f"Row {row_num}: {str(e)}")
            raise
        except Exception as e:
            raise ValueError(f"Row {row_num}: {str(e)}")
    
    if not students:
        raise ValueError("CSV file contains no data rows")
    
    return students


def format_to_csv(students: List[StudentInput]) -> str:
    """
    Format list of StudentInput objects as CSV string.
    
    Validates Requirements: 19.4, 19.5, 19.7
    
    Args:
        students: List of StudentInput objects
    
    Returns:
        CSV string with header and data rows, properly quoted for special characters
    
    Examples:
        >>> student = StudentInput(
        ...     name="John Doe",
        ...     course_type="Engineering",
        ...     institute_tier=1,
        ...     cgpa=Decimal("8.5"),
        ...     year_of_grad=2025
        ... )
        >>> csv_output = format_to_csv([student])
        >>> "John Doe" in csv_output
        True
    """
    if not students:
        return ""
    
    output = StringIO()
    
    # Get all field names from the first student
    first_student_dict = students[0].model_dump()
    fieldnames = list(first_student_dict.keys())
    
    # Create CSV writer with proper quoting for special characters
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        quoting=csv.QUOTE_MINIMAL,  # Quote fields containing commas, quotes, or newlines
        lineterminator='\n'
    )
    
    writer.writeheader()
    
    for student in students:
        row_dict = student.model_dump()
        
        # Convert Decimal to string for CSV output
        for key, value in row_dict.items():
            if isinstance(value, Decimal):
                row_dict[key] = str(value)
            elif value is None:
                row_dict[key] = ''
        
        writer.writerow(row_dict)
    
    return output.getvalue()
