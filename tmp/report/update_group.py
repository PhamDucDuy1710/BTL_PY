from pathlib import Path
from docx import Document
from docx.shared import Pt

root=Path(__file__).resolve().parents[2]
source=root/'output/documents/Bao_cao_nhom_Nhan_dien_khuon_mat.docx'
dest=root/'output/documents/Bao_cao_Nhom_11_Nhan_dien_khuon_mat.docx'
d=Document(source)
replace={
 '[TÊN TRƯỜNG]':'HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG',
 'Nhóm thực hiện: [Số nhóm làm bài]':'Nhóm thực hiện: 11',
 '[Thành viên 1]':'Phạm Đức Duy',
 '[Thành viên 2]':'Lê Đức Anh',
 '[Bổ sung theo nhóm thực tế]':'Lê Thành Trung',
 '[Bổ sung thành viên]':'Lê Thành Trung',
 'Hỗ trợ sinh mã theo yêu cầu chức năng; giải thích mã và cách các thành phần hoạt động.':'Hỗ trợ sinh mã theo yêu cầu chức năng, giải thích mã, tìm và sửa lỗi, thiết kế giao diện và viết báo cáo.',
 '[Công cụ khác nếu có]':'[Các công cụ AI khác đã sử dụng]',
 '[Ghi mục đích thực tế, chẳng hạn tìm lỗi hoặc gợi ý giao diện. Xóa dòng nếu không sử dụng.]':'[Bổ sung đúng tên công cụ và mục đích tương ứng. Không liệt kê công cụ chưa dùng.]'
}
paras=list(d.paragraphs)+[p for t in d.tables for row in t.rows for c in row.cells for p in c.paragraphs]
for p in paras:
 if p.text in replace:
  text=replace[p.text]
  if p.runs:
   p.runs[0].text=text
   for r in p.runs[1:]:r.text=''
  else:p.add_run(text)
 if p.text.startswith('Trong quá trình thực hiện bài tập, nhóm có sử dụng AI'):
  p.text='Trong quá trình thực hiện bài tập, nhóm sử dụng AI hỗ trợ lập trình theo cách thường gọi là “vibe coding”: mô tả chức năng mong muốn bằng ngôn ngữ tự nhiên và sử dụng phần mã do AI đề xuất để phát triển ứng dụng. Nhóm dùng AI để sinh mã, giải thích mã nguồn và luồng xử lý, hỗ trợ tìm và sửa lỗi, thiết kế giao diện, đồng thời soạn thảo báo cáo. AI tham gia trực tiếp vào quá trình xây dựng sản phẩm và tài liệu. Việc sử dụng mã do AI đề xuất vẫn yêu cầu nhóm đọc hiểu, kiểm tra và chịu trách nhiệm về kết quả.'
d.tables[0].rows[3].cells[1].text='[Mã sinh viên]'
for p in d.paragraphs:
 if p.text=='HỌC VIỆN CÔNG NGHỆ BƯU CHÍNH VIỄN THÔNG':
  for r in p.runs:r.bold=True;r.font.size=Pt(12)
d.core_properties.author='Nhóm 11'
d.core_properties.title='Báo cáo Nhóm 11 về hệ thống điểm danh bằng nhận diện khuôn mặt'
d.save(dest)
print(dest)
