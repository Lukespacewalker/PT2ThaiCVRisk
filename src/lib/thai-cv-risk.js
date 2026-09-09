export function calcThaiRisk(age, sex, sbp, dm, chol, smoking) {
  const fullScore =
    0.08183 * age +
    0.39499 * sex +
    0.02084 * sbp +
    0.69974 * dm +
    0.00212 * chol +
    0.41916 * smoking;
  const risk = (1 - Math.pow(0.978296, Math.exp(fullScore - 7.04423))) * 100;
  return Math.max(0, Math.min(100, risk));
}


export function getExtrapolationReasons(age, sbp, chol) {
  const reasons = [];
  if (age < 35 || age > 70) reasons.push("age");
  if (sbp < 80 || sbp > 200) reasons.push("sbp");
  if (chol < 150 || chol > 280) reasons.push("cholesterol");
  return reasons;
}


export function formatExtrapolationLabel(reasons, lang = "th") {
  const labels = lang === "th"
    ? { age: "อายุ", sbp: "SBP", cholesterol: "Total Cholesterol" }
    : { age: "age", sbp: "SBP", cholesterol: "total cholesterol" };
  const reasonText = reasons.map((reason) => labels[reason]).join(", ");
  return lang === "th"
    ? `Extrapolated: ${reasonText} อยู่นอกช่วงอ้างอิงของโมเดล`
    : `Extrapolated: ${reasonText} is outside the model reference range`;
}
