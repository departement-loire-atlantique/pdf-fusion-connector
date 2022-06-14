import base64
import binascii
import datetime
import json
import os
import requests

from collections import OrderedDict

from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_bytes, force_text

from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint

from . import utils

base_dir = os.path.dirname(__file__)
tmp_dir = os.path.join(base_dir, "tmp")

PDF = {
    "type": "object",
    "description": "File object (file0)",
    "required": ["filename", "content_type", "content"],
    "properties": {
        "filename": {
            "type": "string",
            "description": "PDF filename",
        },
        "content_type": {
            "type": "string",
            "description": "MIME content-type",
        },
        "content": {
            "type": "string",
            "description": "Content, base64 encoded",
        },
    },
}

PDFS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "PDFs to merge (5 max)",
    "description": "",
    "type": "object",
    "required": ["pdf1", "pdf2"],
    "properties": OrderedDict(
        {
            "filename": {
                "type": "string",
                "description": "PDF filename",
            },
            "pdf1": PDF,
            "pdf2": PDF,
            "pdf3": PDF,
            "pdf4": PDF,
            "pdf5": PDF,
        }
    ),
}


class FusionPdf(BaseResource):
    category = "Divers"

    class Meta:
        verbose_name = "Connecteur fusion de PDFs"

    @endpoint(
        name="fusion",
        perm="can_access",
        methods=["post"],
        description=_("Merge PDFs files"),
        post={"request_body": {"schema": {"application/json": PDFS_SCHEMA}}},
    )
    def fusion(self, request, post_data):

        pdfs_to_merge = []
        for i in range(1, 6):
            pdfname = f"pdf{i}"
            if post_data.get(pdfname):
                pdf = post_data.get(pdfname) or post_data[pdfname]["filename"]
                pdf_content = base64.b64decode(post_data[pdfname]["content"])
                pdfs_to_merge.append(pdf)

        files_to_merge = []
        for pdf in pdfs_to_merge:
            file = os.path.join(tmp_dir, pdf.get("filename"))
            files_to_merge.append(file)
            with open(file, "wb") as out_file:
                out_file.write(base64.b64decode(pdf.get("content")))

        out_pdf = os.path.join(tmp_dir, "fusion.pdf")
        merged_pdf = utils.concat(files_to_merge, out_file=out_pdf)
        filename = post_data["filename"]

        for file in files_to_merge:
            os.remove(file)

        with open(merged_pdf, "rb") as open_file:
            byte_content = open_file.read()
        base64_bytes = base64.b64encode(byte_content)
        os.remove(merged_pdf)

        file_payload = {}
        file_payload["file"] = {
            "content_type": "application/pdf",
            "filename": filename,
        }
        file_payload["file"]["b64_content"] = force_text(base64_bytes, encoding="ascii")

        return file_payload