"""Reference page listing Idaho bill status codes and their meanings."""

import streamlit as st

st.title("Idaho Bill Status Codes Meaning")

status_table = """
### Bill Status Codes

| Code                       | Meaning                                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------|
| **ADOPTED**                | Resolution or amendment adopted by the chamber                                          |
| **H Agric Aff**            | Referred to the House Agriculture Affairs Committee                                     |
| **H Approp**               | Referred to the House Appropriations Committee (Joint Finance–Appropriations)           |
| **H Bus**                  | Referred to the House Business Committee                                                |
| **H Com/HuRes**            | Referred to the House Commerce & Human Resources Committee                              |
| **H Educ**                 | Referred to the House Education Committee                                               |
| **H Env**                  | Referred to the House Environment Committee                                             |
| **H Filed Office Chief Clerk** | Filed with the House Chief Clerk (officially entered into the record)             |
| **H Gen Ord**              | Placed on the House General Orders calendar (for amendment)                            |
| **H Health/Wel**           | Referred to the House Health & Welfare Committee                                        |
| **H Held at Desk**         | Held at the desk in the House (no further action taken)                                 |
| **H Jud**                  | Referred to the House Judiciary & Rules Committee                                       |
| **H Loc Gov**              | Referred to the House Local Government & Taxation Committee                             |
| **H Rev/Tax**              | Referred to the House Revenue & Taxation Committee                                      |
| **H St Aff**               | Referred to the House State Affairs Committee                                           |
| **H Transp**               | Referred to the House Transportation Committee                                          |
| **H W/M**                  | Referred to the House Ways & Means Committee                                            |
| **H FAILED**               | Failed to pass in the House                                                             |
| **H Res/Con**              | Referred to the House Resources & Conservation Committee                                |
| **LAW**                    | Became law                                                                              |
| **LAW/Line Item Veto**     | Became law, but with one or more line‑item vetoes by the Governor                       |
| **S 3rd Rdg**              | On the Senate Third Reading calendar                                                    |
| **S 3rd Rdgaa**            | On the Senate Third Reading calendar (as amended)                                       |
| **S 14th Ord**             | Placed on the Senate’s 14th Order of Business (General Orders equivalent)               |
| **S Com/HuRes**            | Referred to the Senate Commerce & Human Resources Committee                             |
| **S Educ**                 | Referred to the Senate Education Committee                                              |
| **S Fin**                  | Referred to the Senate Finance Committee                                                |
| **S Health/Wel**           | Referred to the Senate Health & Welfare Committee                                       |
| **S Jud**                  | Referred to the Senate Judiciary & Rules Committee                                      |
| **S Loc Gov**              | Referred to the Senate Local Government & Taxation Committee                            |
| **S Not Concur**           | Senate did not concur with House amendments                                             |
| **S Res/Env**              | Referred to the Senate Resources & Environment Committee                                |
| **S St Aff**               | Referred to the Senate State Affairs Committee                                          |
| **S Transp**               | Referred to the Senate Transportation Committee                                         |
| **S FAILED**               | Failed to pass in the Senate                                                            |
| **VETOED**                 | Vetoed by the Governor                                                                   |
"""

st.markdown(status_table)
