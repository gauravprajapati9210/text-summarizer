import { writeFileSync } from "node:fs";

const apiBaseUrl = (process.env.API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
const config = `// Generated during the Netlify build.\nwindow.TEXT_SUMMARIZER_CONFIG = {\n    apiBaseUrl: ${JSON.stringify(apiBaseUrl)},\n};\n`;

writeFileSync("frontend/config.js", config, "utf8");
console.log(`Frontend configured for API: ${apiBaseUrl}`);
