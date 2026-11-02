from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output'/'documents'
OUT.mkdir(parents=True,exist_ok=True)
d=Document()
s=d.sections[0]
s.page_width=Cm(21); s.page_height=Cm(29.7)
s.top_margin=Cm(2); s.bottom_margin=Cm(2)
s.left_margin=Cm(2.5); s.right_margin=Cm(2)
for name in ['Normal','Title','Heading 1','Heading 2','Caption']:
 st=d.styles[name]; st.font.name='Times New Roman'; st.font.color.rgb=RGBColor(0,0,0)
 st.font.size=Pt({'Normal':12,'Title':23,'Heading 1':17,'Heading 2':13,'Caption':10}[name])
 st.paragraph_format.space_after=Pt(7)
 st.paragraph_format.line_spacing=1.12
d.styles['Normal'].paragraph_format.widow_control=True
for name in ['Heading 1','Heading 2']:
 d.styles[name].font.bold=True
 d.styles[name].paragraph_format.space_before=Pt(9)
 d.styles[name].paragraph_format.keep_with_next=True
s.different_first_page_header_footer=True
p=s.footer.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=p.add_run(); fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
d.core_properties.title='Báo cáo bài tập nhóm về hệ thống điểm danh bằng nhận diện khuôn mặt'
d.core_properties.author='Nhóm thực hiện'
def p(t,style=None):return d.add_paragraph(t,style)
def h(t,l=1):return d.add_heading(t,l)
def page(t):d.add_page_break();h(t)
def table(head,rows,widths=None):
 t=d.add_table(rows=1,cols=len(head));t.style='Table Grid'
 for c,v in zip(t.rows[0].cells,head):c.text=v
 for row in rows:
  for c,v in zip(t.add_row().cells,row):c.text=v
 for i,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
  for c in row.cells:
   for para in c.paragraphs:
    para.paragraph_format.space_after=Pt(4);para.paragraph_format.space_before=Pt(4)
    for r in para.runs:r.font.size=Pt(10.5);r.bold=(i==0)
 if widths:
  t.autofit=False
  for row in t.rows:
   for c,w in zip(row.cells,widths):c.width=Cm(w)
 return t

for text in ['[TÊN TRƯỜNG]','[KHOA HOẶC BỘ MÔN]']:
 q=p(text);q.alignment=WD_ALIGN_PARAGRAPH.CENTER
p('')
q=p('BÁO CÁO BÀI TẬP NHÓM','Title');q.alignment=WD_ALIGN_PARAGRAPH.CENTER
q=p('HỆ THỐNG ĐIỂM DANH\nBẰNG NHẬN DIỆN KHUÔN MẶT','Title');q.alignment=WD_ALIGN_PARAGRAPH.CENTER
p('')
for t in ['Học phần: [Tên học phần]','Giảng viên: [Họ tên giảng viên]','Lớp học phần: [Tên hoặc mã lớp]','Nhóm thực hiện: [Số nhóm làm bài]'] :p(t)
p('')
table(['Họ và tên','Mã sinh viên'],[['[Thành viên 1]','[Mã sinh viên]'],['[Thành viên 2]','[Mã sinh viên]'],['[Bổ sung theo nhóm thực tế]','']],[10,6])
p('')
p('Tháng 10 năm 2026').alignment=WD_ALIGN_PARAGRAPH.CENTER

page('1 Tổng quan bài toán và lựa chọn giải pháp')
h('1.1 Bài toán và mục tiêu',2)
p('Đề tài xây dựng ứng dụng web hỗ trợ ghi nhận sinh viên bằng khuôn mặt từ webcam, kết hợp quản lý lớp, hồ sơ sinh viên và tra cứu lịch sử. Mục tiêu là tạo một quy trình liên tục từ đăng ký dữ liệu khuôn mặt đến nhận diện và lưu thông tin để người quản trị đối chiếu.')
p('Phiên bản hiện tại lưu các lượt nhận diện kèm thời gian và ảnh minh chứng. Hệ thống chưa tổ chức dữ liệu theo môn học hoặc buổi học, chưa tự kết luận có mặt, đi muộn hay vắng. Tên đề tài thể hiện định hướng điểm danh; phạm vi đã triển khai là nền tảng ghi nhận nhận diện phục vụ định hướng đó. [1–3]')
h('1.2 Người dùng và chức năng chính',2)
table(['Đối tượng hoặc chức năng','Nội dung'],[
 ['Quản trị viên','Đăng nhập, quản lý lớp và sinh viên, đăng ký ảnh, xem nhận diện và lịch sử.'],
 ['Sinh viên','Cung cấp ảnh đăng ký và xuất hiện trước camera để hệ thống so khớp.'],
 ['Quản lý dữ liệu','Thêm hoặc cập nhật lớp, hồ sơ sinh viên; xóa sinh viên; chặn xóa lớp còn sinh viên.'],
 ['Theo dõi nhận diện','Video trực tiếp, thông tin người vừa nhận diện, lịch sử có ảnh và thống kê trong ngày.']],[4.6,11.8])
h('1.3 Phân tích lựa chọn giải pháp',2)
p('Kiến trúc web bằng Flask phù hợp với bài tập vì các trang quản lý và API có thể dùng chung logic Python với phần xử lý ảnh. SQLite lưu dữ liệu cục bộ, không yêu cầu triển khai một máy chủ cơ sở dữ liệu riêng. Cấu hình này hướng tới chạy thử trên một máy chủ và một tiến trình ứng dụng.')
p('OpenCV đảm nhận camera và xử lý khung hình. Thư viện face_recognition cung cấp thao tác phát hiện, trích xuất đặc trưng và so sánh khuôn mặt. Sử dụng mô hình có sẵn giúp tập trung vào tích hợp sản phẩm. Đổi lại, chất lượng nhận diện vẫn cần đánh giá trên dữ liệu thực tế; dự án không tự huấn luyện một mô hình nhận diện mới từ đầu.')

page('2 Thiết kế hệ thống')
h('2.1 Kiến trúc và phân chia mô đun',2)
p('Trình duyệt gửi yêu cầu tới Flask để hiển thị trang hoặc lấy dữ liệu API. Ở máy chủ, luồng camera chuyển khung hình tới bộ nhận diện. Bộ nhận diện đối chiếu đặc trưng, lấy thông tin sinh viên và lưu lịch sử khi đủ điều kiện. Ảnh và đặc trưng nằm trên hệ thống tệp; dữ liệu quản lý nằm trong SQLite. [2–6]')
table(['Thành phần','Tệp chính','Trách nhiệm'],[
 ['Giao diện và API','static/; api.py','Trang đăng nhập, quản lý, nhận diện và lịch sử; kiểm tra phiên đăng nhập.'],
 ['Camera','camera_manager.py','Một worker đọc camera, xử lý khung hình và cung cấp video cho nhiều cửa sổ.'],
 ['Nhận diện','recognize.py','So khớp, quyết định chấp nhận, kiểm tra thời gian chờ và ghi lịch sử.'],
 ['Đặc trưng','add_persons.py; feature_store.py','Trích xuất lại toàn bộ hoặc theo sinh viên; khóa cập nhật và thay thế tệp.'],
 ['Cơ sở dữ liệu','db_config.py','Kết nối SQLite, bật khóa ngoại và khởi tạo các bảng.']],[3,5,8.4])
h('2.2 Thiết kế dữ liệu',2)
table(['Bảng','Trường chính và ý nghĩa'],[
 ['admins','id, username, password: tài khoản quản trị và mật khẩu băm.'],
 ['classes','class_id, class_name: danh sách lớp.'],
 ['students','student_id, full_name, class_id: hồ sơ sinh viên; class_id tham chiếu classes.'],
 ['access_logs','id, student_id, timestamp, date_only, snapshot_path: lịch sử và đường dẫn ảnh.']],[3.2,13.2])
p('Quan hệ lớp – sinh viên là một–nhiều. Một sinh viên có thể có nhiều lượt ghi nhận. access_logs lưu student_id để tra cứu và nối dữ liệu, nhưng định nghĩa bảng hiện chưa khai báo khóa ngoại cho trường này. Ảnh đăng ký lưu theo mã sinh viên trong datasets/data; đặc trưng lưu tại datasets/face_features/embeddings.pickle. [5]')

page('3 Quy trình nhận diện và công nghệ')
h('3.1 Đăng ký và cập nhật đặc trưng',2)
p('Người quản trị nhập mã sinh viên, họ tên, lớp và ảnh. API kiểm tra định dạng mã, khả năng giải mã ảnh, kích thước ảnh và yêu cầu đúng một khuôn mặt. Sau khi lưu hồ sơ và ảnh, hệ thống trích xuất lại đặc trưng của sinh viên đó, giữ đặc trưng của những sinh viên khác và nạp lại dữ liệu vào bộ nhớ. Nút Training cho phép cập nhật toàn bộ mẫu. [2, 4]')
h('3.2 Xử lý ảnh từ webcam',2)
p('Mỗi khung hình giảm còn 25% theo cả chiều rộng và chiều cao, sau đó chuyển BGR sang RGB. Chương trình tìm vị trí khuôn mặt, tạo vector đặc trưng và tính khoảng cách với các mẫu đã lưu. Với nhiều mẫu của cùng một sinh viên, chương trình lấy khoảng cách nhỏ nhất, rồi xếp hạng các mã sinh viên theo khoảng cách. [3]')
p('Ứng viên tốt nhất được chấp nhận nếu khoảng cách không vượt 0,52. Khi có ít nhất hai mã sinh viên ứng viên, khoảng cách hạng hai trừ khoảng cách hạng nhất phải đạt tối thiểu 0,05. Trường hợp không đủ điều kiện hiển thị “Không xác định”. Các giá trị này là ngưỡng quyết định trong mã nguồn, không phải xác suất hoặc tỷ lệ chính xác.')
h('3.3 Lưu lịch sử và hạn chế ghi lặp',2)
p('Khi nhận diện hợp lệ, chương trình cắt ảnh khuôn mặt và lưu một bản ghi gồm mã sinh viên, thời gian, ngày và đường dẫn ảnh. Mỗi sinh viên có khoảng chờ 60 giây giữa hai lần lưu. Thời gian chờ nằm trong bộ nhớ tiến trình nên được đặt lại khi khởi động lại ứng dụng. Dashboard đếm các mã sinh viên khác nhau đã ghi nhận trong ngày, không tính kết quả điểm danh theo buổi học.')
h('3.4 Thư viện và công nghệ sử dụng',2)
table(['Công nghệ','Vai trò trong dự án'],[
 ['Python; Flask; Werkzeug','Logic máy chủ, định tuyến, phiên đăng nhập và băm mật khẩu.'],
 ['OpenCV; NumPy','Đọc camera, thay đổi kích thước, chuyển màu, xử lý mảng ảnh.'],
 ['face_recognition; dlib','Phát hiện khuôn mặt, trích xuất và so khớp đặc trưng.'],
 ['SQLite; HTML; CSS; JavaScript','Lưu trữ dữ liệu và xây dựng giao diện web.']],[6,10.4])
p('requirements.txt còn khai báo Pillow, python-dateutil và CMake. Việc xuất hiện trong tệp phụ thuộc không đồng nghĩa mọi thư viện đều tham gia trực tiếp vào luồng nhận diện. [7]')

page('4 Kết quả thực hiện và minh họa sản phẩm')
p('Mã nguồn hiện thực các chức năng đăng nhập, quản lý lớp và sinh viên, đăng ký ảnh, cập nhật đặc trưng, cung cấp luồng camera và tra cứu lịch sử. Giao diện gồm các trang dashboard, students, classes, attendance, history và register. Kết quả này mô tả các thành phần đã có trong chương trình; chưa thay thế đánh giá độ chính xác và tốc độ bằng thử nghiệm. [2–4]')
d.add_picture(str(ROOT/'tmp/report/login.png'),width=Cm(16.3))
p('Hình 1 Giao diện đăng nhập dựng từ mẫu static/login.html; ảnh minh họa giao diện, chưa chứng minh một phiên đăng nhập hoặc nhận diện thành công.','Caption')
h('4.1 Kết quả dự kiến hiển thị khi vận hành',2)
table(['Tình huống','Thông tin hiển thị hoặc lưu'],[
 ['Đăng ký ảnh hợp lệ','Thông báo lưu sinh viên và cập nhật đặc trưng sau khi xử lý hoàn tất.'],
 ['Nhận diện đạt điều kiện','Khung khuôn mặt, mã sinh viên, thông tin vừa nhận diện; bản ghi nếu hết thời gian chờ.'],
 ['Không đủ điều kiện so khớp','Nhãn “Khong xac dinh” trên video.'],
 ['Tra cứu lịch sử','Mã sinh viên, họ tên, lớp, thời gian và ảnh minh chứng.']],[5,11.4])
h('4.2 Minh chứng cần bổ sung sau demo',2)
p('[Chèn ảnh chụp thực tế màn hình đăng ký thành công, nhận diện khuôn mặt và lịch sử tương ứng. Ghi ngày thử, thiết bị, điều kiện ánh sáng và kết quả quan sát. Chỉ dùng ảnh có sự đồng ý của người xuất hiện.]')

page('5 Kiểm thử và kịch bản trình diễn')
h('5.1 Các kiểm thử tự động hiện có',2)
p('Tệp tests/test_api.py định nghĩa năm bài kiểm thử sử dụng cơ sở dữ liệu tạm và Flask test client. Phạm vi tập trung vào API và dữ liệu đầu vào; không đo khả năng nhận diện khuôn mặt. [8]')
table(['Ca kiểm thử','Điều kiện cần kiểm chứng'],[
 ['Truy cập chưa đăng nhập','API và ảnh minh chứng trả 401; video chuyển tới đăng nhập.'],
 ['Trang đăng ký','Người đã đăng nhập mở được trang register.'],
 ['Mã sinh viên không hợp lệ','Từ chối mã chứa ../ trước thao tác ghi dữ liệu.'],
 ['Ảnh không hợp lệ','Trả lỗi 400 và không tạo hồ sơ sinh viên.'],
 ['Cập nhật lớp có sinh viên','Đổi tên lớp thành công, giữ mã lớp đang được tham chiếu.']],[5.1,11.3])
p('Lệnh chạy: python -m unittest discover -s tests -v. Kiểm tra cú pháp JavaScript: node --check static/js/attendance.js. Kết quả chạy và thời điểm: [Điền từ lần chạy thực tế; không tự đánh dấu đạt].')
h('5.2 Các tình huống cần thử với camera thật',2)
p('Cần thử người đã đăng ký, người chưa đăng ký, ánh sáng thay đổi, góc mặt nghiêng và nhiều khuôn mặt. Với mỗi lần thử, ghi kết quả đúng, nhận nhầm hoặc bỏ sót. Thử giữ một người trong khung hình để kiểm tra khoảng chờ, sau đó thử lại sau 60 giây. Chưa có số liệu đủ để kết luận tỷ lệ chính xác hoặc tốc độ xử lý của hệ thống.')
h('5.3 Kịch bản bảo vệ trong 15 phút',2)
table(['Thời lượng','Nội dung'],[
 ['2 phút','Giới thiệu bài toán, mục tiêu và phạm vi đã triển khai.'],
 ['3 phút','Giải thích kiến trúc, dữ liệu và nguyên tắc so khớp.'],
 ['4 phút','Demo đăng nhập, đăng ký, nhận diện và đối chiếu lịch sử.'],
 ['1 phút','Nêu giới hạn, kết luận và vai trò của AI.'],
 ['5 phút','Trả lời câu hỏi và giải thích phần việc từng thành viên.']],[3,13.4])
p('Chuẩn bị môi trường theo README, thiết lập ADMIN_PASSWORD khi tạo database mới và FLASK_SECRET_KEY, chạy python api.py rồi truy cập localhost:5001. Camera nhận diện nằm trên máy chạy server. Mang đầy đủ mã nguồn và dữ liệu cần thiết cho demo. [1, 9]')

page('6 Khai báo sử dụng công cụ AI')
h('6.1 Phạm vi sử dụng AI',2)
p('Trong quá trình thực hiện bài tập, nhóm có sử dụng AI hỗ trợ lập trình theo cách thường gọi là “vibe coding”: mô tả chức năng mong muốn bằng ngôn ngữ tự nhiên và sử dụng phần mã do AI đề xuất để phát triển ứng dụng. Nhóm đồng thời dùng AI giải thích mã nguồn, luồng xử lý và ý nghĩa của các thành phần để hỗ trợ việc tìm hiểu hệ thống. Vì vậy, sản phẩm có sự hỗ trợ của AI trong việc tạo mã, không chỉ ở khâu sửa cách diễn đạt.')
table(['Công cụ','Mục đích và phạm vi'],[
 ['[Tên công cụ AI đã dùng khi lập trình]','Hỗ trợ sinh mã theo yêu cầu chức năng; giải thích mã và cách các thành phần hoạt động.'],
 ['Codex trong cuộc trao đổi này','Đọc và giải thích mã nguồn, hỗ trợ soạn bài thuyết trình tổng quan và nội dung báo cáo.'],
 ['[Công cụ khác nếu có]','[Ghi mục đích thực tế, chẳng hạn tìm lỗi hoặc gợi ý giao diện. Xóa dòng nếu không sử dụng.]']],[5.5,10.9])
h('6.2 Phân biệt hai vai trò của AI',2)
p('AI hỗ trợ phát triển là công cụ hội thoại hoặc trợ lý lập trình dùng để đề xuất và giải thích mã. AI trong sản phẩm là mô hình nhận diện khuôn mặt có sẵn mà thư viện face_recognition/dlib sử dụng. Hai vai trò này khác nhau. Chức năng Training của ứng dụng trích xuất và cập nhật đặc trưng từ ảnh, không huấn luyện lại toàn bộ mô hình và không gọi công cụ hội thoại để nhận diện.')
h('6.3 Trách nhiệm của nhóm đối với mã có AI hỗ trợ',2)
p('Nhóm chịu trách nhiệm về nội dung báo cáo và mã đưa vào sản phẩm. Kết quả giải thích của AI cần được đối chiếu với mã nguồn và kết quả chạy. Khi bảo vệ, mỗi thành viên cần trình bày được phần việc của mình, dữ liệu đầu vào và đầu ra, điều kiện ghi nhận, cùng những giới hạn của giải pháp. Không dùng lời giải thích do AI tạo để thay thế việc hiểu và kiểm chứng chương trình.')
p('Mức độ AI hỗ trợ chưa được quy đổi thành phần trăm vì chưa có nhật ký đủ để đo lường. Việc đã sử dụng AI không tự chứng minh nhóm đã kiểm thử đầy đủ. Minh chứng sử dụng có thể là đoạn hội thoại, prompt và phần mã liên quan, kèm giải thích nhóm đã tiếp nhận hoặc điều chỉnh gì.')
h('6.4 Minh chứng sử dụng cần ghi theo thực tế',2)
p('[Bổ sung 1–2 ví dụ từ hội thoại thật: tên công cụ và thời điểm; yêu cầu gửi cho AI; đoạn mã hoặc lời giải thích nhận được; thao tác kiểm tra hoặc chỉnh sửa của thành viên. Không ghi prompt minh họa thành lịch sử sử dụng thật.]')

page('7 Phân công công việc và đánh giá giới hạn')
h('7.1 Phân công thực tế của từng thành viên',2)
p('Bảng dưới đây cần ghi phần việc thực tế, bao gồm cả việc viết yêu cầu cho AI, đọc và chỉnh sửa mã, chuẩn bị dữ liệu, chạy thử, viết báo cáo hoặc demo. Một chức năng có AI hỗ trợ vẫn cần nêu người trực tiếp làm việc với công cụ và kiểm tra kết quả.')
table(['Thành viên và mã SV','Công việc thực tế','Minh chứng hoặc phần trình bày'],[
 ['[Thành viên 1]','[Điền công việc đã làm]','[Tệp, chức năng, lần thử hoặc nội dung báo cáo]'],
 ['[Thành viên 2]','[Điền công việc đã làm]','[Tệp, chức năng, lần thử hoặc nội dung báo cáo]'],
 ['[Bổ sung thành viên]','[Điền công việc đã làm]','[Minh chứng tương ứng]']],[4,6.2,6.2])
h('7.2 Giới hạn hiện tại',2)
p('Về nghiệp vụ, lịch sử nhận diện chưa liên kết với buổi học và chưa phân loại đi muộn hoặc vắng. Hệ thống cũng không có trường để phân biệt chiều ra và vào, dù giao diện có dùng cụm từ lịch sử ra vào. Về nhận diện, mã nguồn chưa có kiểm tra người thật để chống dùng ảnh hoặc video giả mạo. Các ngưỡng so khớp cần đánh giá bằng dữ liệu thử riêng.')
p('Về vận hành, khóa đặc trưng chỉ đồng bộ các thread trong cùng tiến trình. Cấu hình hiện tại phù hợp chạy một tiến trình server. Trước khi triển khai trên Internet cần bổ sung bảo vệ CSRF, cấu hình máy chủ phù hợp và xem xét quyền truy cập, thời gian lưu ảnh cùng việc bảo vệ dữ liệu sinh trắc học. [1–6]')
h('7.3 Hướng phát triển',2)
p('Ưu tiên bổ sung bảng buổi học và bản ghi điểm danh theo buổi, sau đó xây dựng quy tắc có mặt, đi muộn và vắng. Tiếp theo là đánh giá nhận nhầm, bỏ sót và thời gian xử lý trong nhiều điều kiện. Các cải tiến khác gồm kiểm tra người thật, phân quyền theo vai trò và xuất báo cáo phục vụ giảng viên.')
h('7.4 Kết luận',2)
p('Đề tài kết hợp giao diện web, quản lý dữ liệu và nhận diện khuôn mặt trong một ứng dụng Python. Mã nguồn đã có luồng đăng ký, trích xuất đặc trưng, so khớp webcam và lưu lịch sử có ảnh. AI hỗ trợ việc tạo và giải thích mã trong quá trình phát triển. Để sử dụng như một hệ thống điểm danh hoàn chỉnh, nhóm cần hoàn thiện nghiệp vụ theo buổi học, bổ sung minh chứng thử nghiệm và kiểm soát chất lượng trước khi triển khai rộng hơn.')

page('8 Tài liệu tham chiếu và chuẩn bị hỏi đáp')
h('8.1 Tài liệu tham chiếu',2)
for t in [
 '[1] README.md trong dự án. Phạm vi hiện tại, hướng dẫn chạy và lưu ý triển khai.',
 '[2] api.py và thư mục static. Định tuyến, kiểm tra đăng nhập, quản lý dữ liệu và giao diện.',
 '[3] recognize.py. Lớp FaceRecognizer, so khớp khuôn mặt, thời gian chờ và lưu lịch sử.',
 '[4] add_persons.py. Hàm extract_and_update_features và cập nhật đặc trưng theo sinh viên.',
 '[5] db_config.py. Lược đồ SQLite, khóa ngoại và khởi tạo tài khoản quản trị.',
 '[6] camera_manager.py và feature_store.py. Luồng camera dùng chung và lưu đặc trưng.',
 '[7] requirements.txt. Danh sách thư viện và phiên bản tối thiểu được khai báo.',
 '[8] tests/test_api.py. Các ca kiểm thử tự động cho API.',
 '[9] Thông báo nộp và bảo vệ bài tập nhóm – Nhóm 10. Tệp PDF do giảng viên cung cấp, gồm yêu cầu báo cáo và bảo vệ.'
 ]:p(t)
h('8.2 Các câu hỏi cần giải thích được',2)
table(['Câu hỏi','Ý chính để trả lời'],[
 ['Training có huấn luyện AI mới không?','Không. Hàm xử lý ảnh tạo lại đặc trưng bằng mô hình có sẵn và nạp dữ liệu để so khớp.'],
 ['Vì sao lấy khoảng cách nhỏ nhất theo mã SV?','Một người có nhiều ảnh mẫu. Gộp theo mã để xếp hạng người, tránh so hạng hai với ảnh khác của chính người đó.'],
 ['0,52 và 0,05 có ý nghĩa gì?','Ngưỡng khoảng cách tốt nhất và độ chênh tối thiểu với ứng viên thứ hai; không phải tỷ lệ chính xác.'],
 ['60 giây có bảo đảm điểm danh một lần mỗi buổi?','Không. Đây là thời gian hạn chế ghi lặp; hệ thống chưa có khái niệm buổi học.'],
 ['Nhóm đã dùng AI như thế nào?','Nêu đúng tên công cụ, chức năng được hỗ trợ, người làm việc với AI và cách kiểm chứng thực tế.']],[6.1,10.3])

d.save(OUT/'Bao_cao_nhom_Nhan_dien_khuon_mat.docx')
print(OUT/'Bao_cao_nhom_Nhan_dien_khuon_mat.docx')
