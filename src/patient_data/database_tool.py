from crewai_tools import BaseTool
import sqlite3
import os
import json

class PatientDatabaseRetrievalTool(BaseTool):
    name: str = "Patient Database Retrieval Tool"
    description: str = (
        "Fetches a patient's complete discharge report from a local SQLite database "
        "based on their name. Returns medical, dietary, and follow-up details."
    )

    def _run(self, patient_name: str) -> str:
        """
        Fetches patient discharge details by name from hospital_discharge.db.
        """
        try:
            # Path to local database
            db_path = os.path.join(os.path.dirname(__file__), "hospital_discharge.db")

            if not os.path.exists(db_path):
                return json.dumps({
                    "status": "error",
                    "message": f"Database file not found at {db_path}"
                }, indent=2)

            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Query patient by name (case-insensitive)
            cursor.execute("""
                SELECT patient_name, discharge_date, primary_diagnosis, medications,
                       dietary_restrictions, follow_up, warning_signs, discharge_instructions
                FROM discharge_summaries
                WHERE LOWER(patient_name) = LOWER(?)
            """, (patient_name.strip(),))

            record = cursor.fetchone()
            conn.close()

            if record:
                patient_data = {
                    "patient_name": record[0],
                    "discharge_date": record[1],
                    "primary_diagnosis": record[2],
                    "medications": record[3].split(", "),
                    "dietary_restrictions": record[4],
                    "follow_up": record[5],
                    "warning_signs": record[6],
                    "discharge_instructions": record[7]
                }

                return json.dumps({
                    "status": "success",
                    "data": patient_data
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"No record found for patient '{patient_name}'."
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Database retrieval failed: {str(e)}"
            }, indent=2)


__all__ = ["PatientDatabaseRetrievalTool"]