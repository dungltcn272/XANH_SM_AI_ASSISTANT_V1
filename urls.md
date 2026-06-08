# URL Crawl Registry Draft

Điền URL vào các bảng dưới đây. Mỗi dòng tương ứng một nguồn sẽ được đưa vào `crawl_sources`.

Quy ước:

- `source_profile`: `main_site`, `platform`, `platform_pdf`.
- `source_type`: `web` hoặc `pdf`.
- `category` cũng là thư mục con trong `data/`.
- `enabled`: để `yes` nếu muốn crawler chạy URL đó.

## Main Site - Người Dùng (`data/user`)

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Green SM Car | https://www.greensm.com/vn-vi/greensm-car | service |  |
| yes | Green SM Mini | https://www.greensm.com/vn-vi/greensm-mini | service |  |
| yes | Green SM Premium | https://www.greensm.com/vn-vi/greensm-premium | service |  |
| yes | Green SM Limo | https://www.greensm.com/vn-vi/greensm-limo | service |  |
| yes | Green Airport | https://www.greensm.com/vn-vi/green-airport | service |  |
| yes | Green Tour | https://www.greensm.com/vn-vi/green-tour | service |  |
| yes | Green Gift Card | https://www.greensm.com/vn-vi/green-gift-card | service |  |
| yes | Green Liên Tỉnh | https://www.greensm.com/vn-vi/green-lien-tinh | service |  |
| yes | Green SM Bike | https://www.greensm.com/vn-vi/greensm-bike | service |  |
| yes | Green SM Ngon | https://www.greensm.com/vn-vi/greensm-ngon | service |  |
| yes | Green Express | https://www.greensm.com/vn-vi/green-express | service | Ưu tiên phí/giá cước |
| yes | Green Van | https://www.greensm.com/vn-vi/green-van | service |  |
| yes | Green Subscription | https://www.greensm.com/vn-vi/green-subscription | service |  |
| yes |  |  | service | Dán thêm URL tại đây |

## Main Site - Merchant (`data/merchant`)

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Green Subscription | https://www.greensm.com/vn-vi/green-subscription | service |  |
| yes | Green SM Merchant | https://www.greensm.com/vn-vi/greensm-merchant | service |  |
| yes | Business Payment | https://www.greensm.com/vn-vi/business-payment | service |  |
| yes |  |  | service | Dán thêm URL tại đây |

## Main Site - Driver (`data/driver`)

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Driver Car | https://www.greensm.com/vn-vi/driver-car | driver |  |
| yes | Driver Bike | https://www.greensm.com/vn-vi/driver-bike | driver |  |
| yes | Driver Platform | https://www.greensm.com/vn-vi/driver-platform | driver |  |
| yes | Driver Center | https://www.greensm.com/vn-vi/driver-center | driver |  |
| yes |  |  | driver | Dán thêm URL tại đây |

## Main Site - Green Care (`data/green-care`)

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Bảo hiểm khách hàng | https://www.greensm.com/vn-vi/bao-hiem-khach-hang | policy |  |
| yes | Bảo hiểm hàng hóa Xanh Express | https://www.greensm.com/vn-vi/bao-hiem-hang-hoa-xanh-express | policy |  |
| yes | Bảo hiểm giao đồ ăn | https://www.greensm.com/vn-vi/bao-hiem-giao-do-an | policy |  |
| yes |  |  | policy | Dán thêm URL tại đây |

## Main Site - Helps (`data/helps`)

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Helps | https://www.greensm.com/vn-vi/helps | faq | Trang dài, không đưa cả trang vào một LLM call |
| yes |  |  | faq | Dán thêm URL tại đây |

## Main Site - Terms And Policies (`data/term-policies`)

| enabled | title | url | source_type | document_type | notes |
|---|---|---|---|---|---|
| yes | Điều khoản chung | https://www.greensm.com/vn-vi/terms-policies/general | web | policy |  |
| yes | Quy định dạng PDF/main site | https://www.greensm.com/vn-vi/terms-policies/regulations | pdf | policy_pdf | Cần kiểm tra đây là PDF thật hay page sinh PDF |
| yes | Privacy Notice | https://www.greensm.com/vn-vi/terms-policies/privacy-notice | web | policy |  |
| yes | Service Agreement | https://www.greensm.com/vn-vi/terms-policies/service-agreement | web | policy |  |
| yes | Consumer Protection Policy | https://www.greensm.com/vn-vi/terms-policies/consumer-protection-policy | web | policy |  |
| yes |  |  | web | policy | Dán thêm URL tại đây |

## Platform - Trang Xe / Policy Web / News (`data/platform`)

Các URL platform web dùng:

- `source_profile=platform`
- `source_type=web`
- `category=platform`

| enabled | title | url | document_type | notes |
|---|---|---|---|---|
| yes | Platform Home | https://platform.greensm.com/VN-vi | overview |  |
| yes | News Listing | https://platform.greensm.com/VN-vi/news/all/page/1 | news | Chỉ dùng catalog/audit, không thay thế detail |
| yes |  |  | vehicle | Dán URL trang xe mua/thuê tại đây |
| yes |  |  | policy_page | Dán URL chính sách web platform tại đây |
| yes |  |  | news | Dán URL detail `/news/<slug>` tại đây |
| yes |  |  | vehicle |  |
| yes |  |  | policy_page |  |
| yes |  |  | news |  |

## Platform - PDF Chính Sách (`data/platform`)

Các URL PDF platform dùng:

- `source_profile=platform_pdf`
- `source_type=pdf`
- `category=platform`
- `document_type=policy_pdf`

| enabled | title | url | notes |
|---|---|---|---|
| yes | Chương trình mua xe ô tô điện VinFast trực tiếp qua Green SM | https://platform-static-staging.car-trading.gsm-api.net/public/document/Chuong_trinh_mua_xe_oto_dien_vinfast_truc_tiep_qua_green_sm.pdf | PDF 7 trang, phải extract đủ |
| yes | Chương trình thuê vận hành/thưởng vận doanh xe ô tô điện VinFast | https://platform-static-staging.car-trading.gsm-api.net/public/document/Chuong_trinh_thue_van_hanh_thuong_van_doanh_xe_o_to_dien_vinfast.pdf |  |
| yes | Chương trình cho thuê xe ô tô điện GSM Rental | https://platform-static.car-trading.gsm-api.net/public/document/Chuong_trinh_cho_thue_xe_o_to_dien_gsm_rental.pdf |  |
| yes | Chính sách bán xe máy điện VinFast | https://platform-static.car-trading.gsm-api.net/public/document/Chinh_sach_ban_xe_may_dien_vinfast.pdf |  |
| yes |  |  | Dán thêm URL PDF tại đây |

## Overview Generated Docs (`data/overview`)

Các file này không cần URL crawl thật; backend sinh từ manifest/frontmatter/registry.

| enabled | title | output_file | document_type | notes |
|---|---|---|---|---|
| yes | Service Catalog | data/overview/service_catalog.md | overview | Trả lời câu hỏi tổng quát Green SM gồm gì |
| yes | Pricing Catalog | data/overview/pricing_catalog.md | overview | Tổng hợp giá/phí |
| yes | Platform Vehicle Catalog | data/overview/platform_vehicle_catalog.md | overview | Tổng hợp xe platform |
| yes | Policy Catalog | data/overview/policy_catalog.md | overview | Tổng hợp chính sách |
| yes | News Catalog | data/overview/news_catalog.md | overview | Tổng hợp news detail đã có URL |
