# Evaluation report

Cases: **17**  
Decision accuracy: **100%**  
Reason recall (expected reasons the agent gave): **100%**  
Unsafe records (must be 0): **0**  
False flags: 0 · Missed flags: 0  
Explanation rule checks passed: **100%**  
Avg tool calls per invoice: 3.9 · Avg time per invoice: 49.7 ms

| Case | Expected | Got | OK | Reasons found | Tools called |
|---|---|---|---|---|---|
| 01_clean_needs_approval | needs_approval | needs_approval | yes | - | 4 |
| 02_duplicate_of_paid | flagged | flagged | yes | 1/1 | 4 |
| 03_unapproved_vendor | flagged | flagged | yes | 1/1 | 4 |
| 04_over_single_invoice_limit | flagged | flagged | yes | 1/1 | 4 |
| 05_over_remaining_budget | flagged | flagged | yes | 1/1 | 4 |
| 06_total_mismatch | flagged | flagged | yes | 1/1 | 4 |
| 07_small_clean | recorded | recorded | yes | - | 5 |
| 08_missing_vendor_id | flagged | flagged | yes | 1/1 | 1 |
| 09_unknown_vendor | flagged | flagged | yes | 1/1 | 4 |
| 10_alternate_layout_clean | recorded | recorded | yes | - | 5 |
| 11_exactly_at_threshold | needs_approval | needs_approval | yes | - | 4 |
| 12_just_under_threshold | recorded | recorded | yes | - | 5 |
| 13_several_problems | flagged | flagged | yes | 3/3 | 4 |
| 14a_first_copy | recorded | recorded | yes | - | 5 |
| 14b_resubmitted_copy | flagged | flagged | yes | 1/1 | 4 |
| 15_department_without_policy | flagged | flagged | yes | 1/1 | 4 |
| 16_scanned_image_no_text | flagged | flagged | yes | 1/1 | 1 |
