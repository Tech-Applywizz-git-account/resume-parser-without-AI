from parser import ResumeParser

sample_text = """
John Quincy Doe
Email: john.doe@example.com
Phone: +1 555-123-4567
LinkedIn: https://www.linkedin.com/in/johndoe
GitHub: https://github.com/johndoe
Portfolio: https://johndoe.com

Education
Bachelor of Computer Science
Harvard University, 2012
CGPA: 3.8

Experience
Senior Software Engineer
Tech Corp
June 2018 - December 2023
- Led a team of developers.

Software Developer
Innovate LLC
August 2012 - Present
- Developed web applications.

Summary of experience: 10 years in full-stack development...
"""

parser = ResumeParser(sample_text)
result = parser.parse()

import json
print(json.dumps(result, indent=2))
