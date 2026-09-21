import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import {fileURLToPath} from "node:url";
export default defineConfig({base:"/ventas/",plugins:[react()],resolve:{alias:{"@":fileURLToPath(new URL(".",import.meta.url))}},build:{outDir:"../../ventas",emptyOutDir:true},server:{allowedHosts:["terminal.local"]}});
