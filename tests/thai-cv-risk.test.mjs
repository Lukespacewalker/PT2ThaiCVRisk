import assert from "node:assert/strict";
import test from "node:test";


test("calculates an out-of-range score and tags each extrapolated input", async () => {
  let risk;
  try {
    risk = await import("../src/lib/thai-cv-risk.js");
  } catch (error) {
    assert.fail(`Thai CV Risk browser module is missing: ${error.message}`);
  }

  assert.equal(risk.calcThaiRisk(27, 1, 204, 0, 354, 0).toFixed(2), "3.78");
  assert.deepEqual(risk.getExtrapolationReasons(27, 204, 354), [
    "age",
    "sbp",
    "cholesterol",
  ]);
  assert.equal(
    risk.formatExtrapolationLabel(["age", "sbp", "cholesterol"], "th"),
    "Extrapolated: อายุ, SBP, Total Cholesterol อยู่นอกช่วงอ้างอิงของโมเดล",
  );
});
