from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from sim_buah_api.database import db
from sim_buah_api.models import BarangKeluar, BarangMasuk, DetailKeluar, BatchStok, Supplier
from datetime import datetime
import pandas as pd
import io

# Untuk ReportLab PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

laporan_bp = Blueprint('laporan', __name__, url_prefix='/api/laporan')

# ========================== HELPERS ==========================

def get_transaksi_data(start_date, end_date):
    keluar_qs = BarangKeluar.query.filter(
        BarangKeluar.tanggal_transaksi.between(start_date, end_date)
    ).all()
    transaksi_keluar = [{
        "id": row.keluar_id,
        "tanggal": row.tanggal_transaksi.strftime("%Y-%m-%d"),
        "tipe": "Keluar",
        "pihak": row.pembeli.nama_pelanggan if row.pembeli else "N/A",
        "total": float(row.total_penjualan) if row.total_penjualan is not None else 0.00,
        "status": row.status_pesanan
    } for row in keluar_qs]

    masuk_qs = BarangMasuk.query.filter(
        BarangMasuk.tanggal_transaksi.between(start_date, end_date)
    ).all()
    transaksi_masuk = [{
        "id": row.masuk_id,
        "tanggal": row.tanggal_transaksi.strftime("%Y-%m-%d"),
        "pihak": row.pemasok.nama_supplier if row.pemasok else "N/A",
        "tipe": "Masuk",
        "total": float(row.total_biaya) if row.total_biaya is not None else 0.00,
        "status": "Selesai"
    } for row in masuk_qs]
    
    all_transactions = sorted(transaksi_keluar + transaksi_masuk, key=lambda x: x['tanggal'], reverse=True)
    return all_transactions

def get_penjualan_data(start_date, end_date):
    raw_data = db.session.query(
        BarangKeluar.tanggal_transaksi,
        db.func.sum(BarangKeluar.total_penjualan).label('total_penjualan'),
        db.func.count(BarangKeluar.keluar_id).label('jumlah_transaksi')
    ).filter(
        BarangKeluar.tanggal_transaksi.between(start_date, end_date)
    ).group_by(
        BarangKeluar.tanggal_transaksi
    ).order_by(
        BarangKeluar.tanggal_transaksi.desc()
    ).all()

    data = [{
        "tanggal": row.tanggal_transaksi.strftime("%Y-%m-%d"),
        "total_penjualan": float(row.total_penjualan) if row.total_penjualan is not None else 0.00,
        "jumlah_transaksi": row.jumlah_transaksi
    } for row in raw_data]
    return data

# ========================== ENDPOINT JSON ==========================

@laporan_bp.route("/transaksi", methods=["GET", "OPTIONS"])
@jwt_required()
def laporan_transaksi_json():
    if request.method == "OPTIONS":
        return jsonify({}), 200 # <-- FIX: OPTIONS diizinkan

    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        data = get_transaksi_data(start_date, end_date)
        
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching data: {str(e)}"}), 500


@laporan_bp.route("/penjualan", methods=["GET", "OPTIONS"])
@jwt_required()
def laporan_penjualan_json():
    if request.method == "OPTIONS":
        return jsonify({}), 200 # <-- FIX: OPTIONS diizinkan

    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        data = get_penjualan_data(start_date, end_date)
        
        return jsonify({"status": "success", "data": data}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching data: {str(e)}"}), 500

# ========================== ENDPOINT EXPORT ==========================

@laporan_bp.route("/export/<string:report_type>", methods=["GET", "OPTIONS"])
@jwt_required()
def export_laporan(report_type):
    if request.method == "OPTIONS":
        return jsonify({}), 200 # <-- FIX: OPTIONS diizinkan

    report_format = request.args.get('format', 'excel')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except:
        return jsonify({"error": "Format tanggal tidak valid (YYYY-MM-DD)"}), 400

    try: 
        # 1. Ambil data
        if report_type == 'transaksi':
            data = get_transaksi_data(start_date, end_date)
            df = pd.DataFrame(data)
            file_name = f"Laporan_Transaksi_{start_date}_to_{end_date}"
        elif report_type == 'penjualan':
            data = get_penjualan_data(start_date, end_date)
            df = pd.DataFrame(data)
            file_name = f"Laporan_Penjualan_{start_date}_to_{end_date}"
        else:
            return jsonify({"error": "Tipe laporan tidak dikenal"}), 400

        # Inisialisasi response
        response = None 

        # 2. LOGIKA EXPORT
        if report_format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Laporan')
            output.seek(0)
            response = send_file(output, as_attachment=True, download_name=f"{file_name}.xlsx",
                                 mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        elif report_format == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig') 
            csv_bytes = output.getvalue().encode('utf-8-sig')
            response = send_file(io.BytesIO(csv_bytes), as_attachment=True, download_name=f"{file_name}.csv",
                                 mimetype='text/csv')

        elif report_format == 'pdf':
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()

            elements.append(Paragraph(file_name, styles['Title']))
            elements.append(Spacer(1, 12)) 
            header_row = df.columns.tolist()
            data_rows = df.values.tolist()
            data_table = [header_row] + data_rows
            col_widths = [doc.width/len(header_row)] * len(header_row)

            table = Table(data_table, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#047857')), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                ('BOX', (0,0), (-1,-1), 0.25, colors.black),
            ]))
            elements.append(table)
            doc.build(elements)
            pdf_buffer.seek(0)

            response = send_file(pdf_buffer, as_attachment=True, download_name=f"{file_name}.pdf",
                                 mimetype='application/pdf')
                                 
        else:
            return jsonify({"error": "Format export tidak didukung"}), 400

        # HANYA RETURN RESPONSE, header akan ditambahkan oleh app.py hook
        return response 

    except Exception as e:
        # HANYA RETURN ERROR, header akan ditambahkan oleh app.py hook
        print(f"EXPORT CRASHED: {e}") 
        return jsonify({"status": "error", "message": f"Server crash saat export: {str(e)}"}), 500