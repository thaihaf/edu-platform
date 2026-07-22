# Product Vision

## Tuyên bố sản phẩm

Xây dựng một nền tảng AI có thể biến một mục tiêu học tập cùng một số nguồn ban đầu thành một khóa học có chứng cứ, có khả năng cập nhật và có hệ thống đánh giá chất lượng.

Ví dụ:

> Người dùng muốn ôn thi/phỏng vấn Chuyên viên phát triển phần mềm Agribank.

Hệ thống phải tự:

- Hiểu tổ chức, vị trí, kỳ thi, thời gian và mức độ người học.
- Tìm thông báo chính thức, JD, review đề thi, review phỏng vấn, tài liệu ôn thi, thông tin công nghệ và nghiệp vụ liên quan.
- Xác định cấu trúc đề, dạng câu hỏi, chủ đề trọng tâm, khác biệt theo từng năm.
- Phát hiện câu hỏi được báo cáo là từng xuất hiện.
- Tạo câu hỏi mới từ JD và kiến thức chuẩn.
- Gắn citation và confidence.
- Tạo lộ trình, lesson, quiz, flashcard và mock interview.
- Cho phép người quản trị duyệt, sửa, publish và rollback.

## Nguyên tắc không được vi phạm

1. AI không được tuyên bố một câu hỏi từng xuất hiện nếu không có nguồn.
2. Mọi claim quan trọng phải có evidence.
3. Nguồn sao chép không được tính là nguồn độc lập.
4. Nội dung AI sinh phải được phân biệt rõ với nội dung được báo cáo thực tế.
5. Không tự động ghi đè khóa học đã publish.
6. Mọi thay đổi phải tạo version hoặc draft.
7. Không vượt paywall, CAPTCHA, nhóm kín hoặc cơ chế kiểm soát truy cập.
8. Chỉ thu thập dữ liệu công khai và hợp pháp.
9. Mỗi output AI phải lưu model, prompt version, source set và timestamp.
10. Thiết kế domain-agnostic: thêm môn học không cần thêm table hoặc sửa code.

## Personas

### Research Admin
- Tạo mục tiêu nghiên cứu.
- Thêm URL/file/text.
- Cấu hình độ sâu.
- Duyệt nguồn.
- Duyệt evidence.
- Duyệt course draft.
- Duyệt question bank.
- Publish version.

### Learner
- Học theo lộ trình.
- Làm quiz.
- Xem nguồn.
- Hỏi AI tutor.
- Làm mock interview.
- Theo dõi chủ đề yếu.

### Reviewer
- Kiểm tra claim.
- Kiểm tra đáp án.
- Đánh dấu ambiguity.
- Xử lý source conflict.

## MVP success criteria

- Tạo được một khóa học Agribank CNTT từ mô tả + 5 URL.
- Tự tìm thêm ít nhất 20 nguồn liên quan.
- Phân loại nguồn official/review/training/blog/document.
- Tạo ít nhất 8 module.
- Tạo ít nhất 100 câu hỏi với origin type.
- Citation coverage đạt 100% với claim quan trọng.
- Có draft/publish/version/rollback.
- Có background job và retry.
