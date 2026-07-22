# AI Course Research Platform — Codex Execution Kit

Bộ tài liệu này giúp Codex xây dựng tuần tự một nền tảng nghiên cứu sâu và tạo khóa học bằng AI từ:

- Mô tả tự do
- URL
- PDF/DOCX/PPTX/XLSX
- Nội dung dán trực tiếp
- JD tuyển dụng
- Bài review
- Tài liệu đề thi
- Nguồn web do AI tự tìm thêm

Mục tiêu không phải là một LMS truyền thống. Lõi sản phẩm là một **AI Research & Assessment Engine** có khả năng:

1. Hiểu mục tiêu học tập.
2. Lập kế hoạch nghiên cứu.
3. Tìm nguồn sâu bằng nhiều chiến lược tìm kiếm.
4. Crawl và chuẩn hóa dữ liệu.
5. Xây evidence graph và skill graph.
6. Phân biệt câu hỏi thật, câu hỏi suy luận và câu hỏi AI sinh.
7. Tạo khóa học, bài học, ngân hàng câu hỏi và mock interview.
8. Kiểm định chất lượng bằng nhiều reviewer độc lập.
9. Lưu citation, source lineage, confidence và version.
10. Cập nhật khóa học bằng diff mà không sửa code hay database thủ công.

## Stack mặc định

- Python 3.12
- FastAPI
- SQLAlchemy 2 + Alembic
- PostgreSQL + pgvector
- Redis
- Celery cho MVP, có thể nâng cấp Temporal
- LangGraph
- SearXNG
- Crawl4AI hoặc Firecrawl adapter
- Browser-use adapter
- Docling
- OpenSearch ở phase sau
- Neo4j ở phase sau
- DeepEval
- Frontend: Next.js hoặc bất kỳ framework phù hợp; backend không phụ thuộc framework UI

## Cách dùng với Codex

1. Mở repository mới.
2. Copy toàn bộ kit vào repo.
3. Đọc `codex/MASTER_PROMPT.md`.
4. Chạy lần lượt các prompt trong `codex/phases`.
5. Sau mỗi phase, yêu cầu Codex:
   - chạy test,
   - cập nhật changelog,
   - ghi ADR,
   - dừng nếu acceptance criteria chưa đạt.
6. Không cho Codex nhảy phase.

## Thứ tự triển khai

1. Foundation
2. Data model
3. Source ingestion
4. Search and crawling
5. Research orchestration
6. Evidence and knowledge
7. Course generation
8. Question generation
9. Evaluation
10. Admin web
11. Learner web
12. Production hardening
