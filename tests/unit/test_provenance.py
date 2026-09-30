"""Unit tests for provenance tracking and ParameterRecord."""

import unittest
from steelcq.provenance.record import ParameterRecord, SourceType, ValidationStatus, ProvenanceTracker


class TestProvenance(unittest.TestCase):
    def test_parameter_record_creation(self):
        rec = ParameterRecord(
            name="martensite_start_temp",
            value=325.0,
            unit="degC",
            source="Andrews (1965) JISI",
            source_type=SourceType.LITERATURE,
            uncertainty=10.0,
            applicability="Medium carbon low alloy steels",
            calibration_status="calibrated",
            validation_status=ValidationStatus.VALIDATED
        )
        self.assertEqual(rec.name, "martensite_start_temp")
        self.assertEqual(rec.value, 325.0)
        self.assertEqual(rec.unit, "degC")
        self.assertEqual(rec.source_type, SourceType.LITERATURE)

    def test_empty_parameter_record_fails(self):
        with self.assertRaises(ValueError):
            ParameterRecord(
                name="",
                value=10.0,
                unit="degC",
                source="test",
                source_type=SourceType.LITERATURE
            )

    def test_provenance_tracker(self):
        tracker = ProvenanceTracker()
        rec = ParameterRecord(
            name="austenite_grain_size",
            value=25.0,
            unit="um",
            source="ASTM E112",
            source_type=SourceType.EXPERIMENTAL,
            validation_status=ValidationStatus.VALIDATED
        )
        tracker.register(rec)
        self.assertEqual(tracker.get("austenite_grain_size").value, 25.0)
        summary = tracker.audit_summary()
        self.assertEqual(summary["VALIDATED"], 1)


if __name__ == "__main__":
    unittest.main()
