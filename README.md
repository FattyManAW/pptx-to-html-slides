# PPT 轉 HTML 投影片轉換專案

## 說明
將 PowerPoint (.pptx) 檔案轉換為自包含的 HTML 投影片格式。

## 原始檔案
- `APS AI Agent 智能体解决方案_20260113.pptx` → 12 張投影片
- `CRIS IMPACTs 双碳管理系统_202601_V2.0.pptx` → 36 張投影片
- `润思IMPACTS APS生态伙伴解决方案_202601V2.0.pptx` → 62 張投影片

## 輸出
- `html/aps-ai-agent.html` — APS AI Agent 智能體應用場景介紹
- `html/cris-impacts-carbon.html` — IMPACTs 雙碳數位化管理系統
- `html/runs-impacts-aps-partner.html` — IMPACTS APS 智能先進排程系統

## 使用方式
```bash
python3 pptx2html.py <input.pptx> <output.html> --title "投影片標題"
```

## 功能
- 提取文字（含字體、顏色、對齊）
- 提取並內嵌圖片（base64）
- 保留主題色（theme colors）
- 鍵盤導航：← → Space PageUp PageDown Home End F
- 觸控滑動支援
- 單一 HTML 檔案，無需外部依賴

## 任務要求
- 保留母片格式，內容轉換為更漂亮更專業的 HTML 樣式
- 結合 HTML 投影片的詳細細節
- 完全遵守官方手冊規定
- GitHub 記錄所有內容
