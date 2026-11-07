"""The evaluation set: synthetic invoices with the answer a careful accounts-payable clerk would give.

Each case says what the PDF contains and what the agent must decide. Cases are processed in order
against one fresh ledger, so a later case can depend on an earlier one (see the in-batch duplicate).
"""

# label sets, to check extraction isn't tied to one invoice layout
STANDARD = {"number": "Invoice Number", "date": "Invoice Date", "dept": "Bill To Department", "total": "Total Due"}
ALTERNATE = {"number": "Invoice #", "date": "Date", "dept": "Department", "total": "Total"}

CASES = [
    # id, vendor_id, vendor_name, invoice_number, department, line items, printed total, labels, expected, must mention
    {"id": "01_clean_needs_approval", "vendor_id": "V002", "vendor": "CloudHost LLC", "number": "INV-3001",
     "dept": "Engineering", "items": [("Cloud hosting - October", 1, 1800.00)],
     "expect": "needs_approval", "mentions": []},
    {"id": "02_duplicate_of_paid", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1001",
     "dept": "Engineering", "items": [("Office chairs", 5, 250.00)],
     "expect": "flagged", "mentions": ["already in the ledger"]},
    {"id": "03_unapproved_vendor", "vendor_id": "V003", "vendor": "Unknown Consulting", "number": "INV-7001",
     "dept": "Marketing", "items": [("Strategy workshop", 1, 900.00)],
     "expect": "flagged", "mentions": ["not approved"]},
    {"id": "04_over_single_invoice_limit", "vendor_id": "V002", "vendor": "CloudHost LLC", "number": "INV-3002",
     "dept": "Engineering", "items": [("GPU reserved instances", 3, 2400.00)],
     "expect": "flagged", "mentions": ["single-invoice limit"]},
    {"id": "05_over_remaining_budget", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1050",
     "dept": "Marketing", "items": [("Trade show booth supplies", 1, 1500.00)],
     "expect": "flagged", "mentions": ["remaining budget"]},
    {"id": "06_total_mismatch", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1051",
     "dept": "Engineering", "items": [("Printer paper", 10, 45.00), ("Toner", 2, 120.00)], "total": 790.00,
     "expect": "flagged", "mentions": ["line items add up"]},
    {"id": "07_small_clean", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1052",
     "dept": "Engineering", "items": [("Whiteboard markers", 12, 20.00)],
     "expect": "recorded", "mentions": []},
    {"id": "08_missing_vendor_id", "vendor_id": None, "vendor": "CloudHost LLC", "number": "INV-3003",
     "dept": "Engineering", "items": [("Backup storage", 1, 300.00)],
     "expect": "flagged", "mentions": ["missing field: vendor_id"]},
    {"id": "09_unknown_vendor", "vendor_id": "V999", "vendor": "Brand New Vendor Inc", "number": "BNV-1",
     "dept": "Engineering", "items": [("Consulting hours", 4, 150.00)],
     "expect": "flagged", "mentions": ["not in the ledger"]},
    {"id": "10_alternate_layout_clean", "vendor_id": "V002", "vendor": "CloudHost LLC", "number": "INV-3004",
     "dept": "Engineering", "items": [("DNS hosting", 1, 120.00)], "labels": ALTERNATE,
     "expect": "recorded", "mentions": []},
    {"id": "11_exactly_at_threshold", "vendor_id": "V002", "vendor": "CloudHost LLC", "number": "INV-3005",
     "dept": "Engineering", "items": [("Load balancer", 1, 1000.00)],
     "expect": "needs_approval", "mentions": []},
    {"id": "12_just_under_threshold", "vendor_id": "V002", "vendor": "CloudHost LLC", "number": "INV-3006",
     "dept": "Engineering", "items": [("Monitoring", 1, 999.99)],
     "expect": "recorded", "mentions": []},
    {"id": "13_several_problems", "vendor_id": "V003", "vendor": "Unknown Consulting", "number": "INV-7002",
     "dept": "Marketing", "items": [("Brand campaign", 1, 2500.00)],
     "expect": "flagged", "mentions": ["not approved", "single-invoice limit", "remaining budget"]},
    {"id": "14a_first_copy", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1060",
     "dept": "Engineering", "items": [("Desk lamps", 4, 35.00)],
     "expect": "recorded", "mentions": []},
    {"id": "14b_resubmitted_copy", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1060",
     "dept": "Engineering", "items": [("Desk lamps", 4, 35.00)],
     "expect": "flagged", "mentions": ["already in the ledger"]},
    {"id": "15_department_without_policy", "vendor_id": "V001", "vendor": "Acme Office Supply", "number": "INV-1070",
     "dept": "Legal", "items": [("Binders", 10, 8.00)],
     "expect": "flagged", "mentions": ["no spending policy"]},
    {"id": "16_scanned_image_no_text", "scanned": True,
     "expect": "flagged", "mentions": ["no text found"]},
]
