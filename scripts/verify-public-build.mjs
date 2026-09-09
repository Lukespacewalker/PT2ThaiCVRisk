import fs from "node:fs";
import path from "node:path";


const root = process.cwd();
const distDir = path.join(root, "dist");
const privatePage = path.join(distDir, "private", "index.html");

if (!fs.existsSync(privatePage)) {
  throw new Error("Public build is missing the guarded /private route");
}

const privateHtml = fs.readFileSync(privatePage, "utf8");
if (!privateHtml.includes("Redirecting to: /")) {
  throw new Error("Public build did not replace /private with a redirect");
}

const privateData = path.join(root, "src", "data", "thai_cv_data_private.json");
if (fs.existsSync(privateData)) {
  const names = JSON.parse(fs.readFileSync(privateData, "utf8"))
    .map((record) => record.name)
    .filter(Boolean);
  const files = [];
  const visit = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(fullPath);
      else files.push(fullPath);
    }
  };
  visit(distDir);

  for (const file of files) {
    const content = fs.readFileSync(file);
    const text = content.toString("utf8");
    const leakedName = names.find((name) => text.includes(name));
    if (leakedName) {
      throw new Error(`Private name leaked into public artifact: ${path.relative(root, file)}`);
    }
  }
}

console.log("Public build privacy scan passed");
