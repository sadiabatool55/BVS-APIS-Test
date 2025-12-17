from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# 🔗 API URLs
LOGIN_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/RetailerBVSLogin"

# Account Registration
ACCOUNT_REG_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSAccountRegistration/OTP"

# Cash Deposit
CASH_DEPOSIT_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCashDeposit/CashDepositBVS"
CASH_DEPOSIT_CONFIRM_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCashDeposit/CashDepositBVS/Confirmation"

# CNIC to MA
CNIC_TO_MA_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCNICtoMA/CNICtoMABVS"
CNIC_TO_MA_CONFIRM_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCNICtoMA/CNICtoMABVSConfirmation"

# Cash Withdrawal
CASH_WITHDRAWAL_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCashWithdrawal/CashWithdrawalBVS"
CASH_WITHDRAWAL_CONFIRM_URL = "https://rgw.8798-f464fa20.eu-de.ri1.apiconnect.appdomain.cloud/tmfb/dev-catalog/BVSCashWithdrawal/CashWithdrawalBVS/Confirmation"

CLIENT_HEADERS = {
    "X-IBM-Client-Id": "924726a273f72a75733787680810c4e4",
    "X-IBM-Client-Secret": "7154c95b3351d88cb31302f297eb5a9c",
    "X-Channel": "bvsgateway",
    "Content-Type": "application/json"
}


@app.route("/bvs")
def index():
    return render_template("index.html")


@app.route("/run-apis", methods=["GET"])
def run_apis():
    results = {}

 # 1️⃣ LOGIN (now printing in frontend)
    login_payload = {
        "OTP": "491765",
        "User": "923431664399@1010",
        "Pin": "12121"
    }
    login_resp = requests.post(LOGIN_URL, headers=CLIENT_HEADERS, json=login_payload)
    login_json = safe_json(login_resp)

    # ✅ Show login response in frontend
    results["Login"] = login_json

    if login_resp.status_code != 200:
        return jsonify(results)

    auth_token = login_json.get("AccessToken")
    session_id = login_json.get("SessionID")
    if not auth_token or not session_id:
        return jsonify({"error": "AccessToken/SessionID missing from login response"})

    dynamic_headers = CLIENT_HEADERS.copy()
    dynamic_headers["Authorization"] = f"Bearer {auth_token}"
    dynamic_headers["Sessionid"] = session_id
    dynamic_headers["X-Username"] = "923482665224@2900"
    dynamic_headers["X-Password"] = "12121"

    # 2️⃣ ACCOUNT REGISTRATION - LEG 1
    acc_reg_payload_leg1 = {
        "TransactionID": "0",
        "Longitude": "31.5686808",
        "Latitude": "74.3000874",
        "CustomerCNIC": "3740567242112",
        "CustomerMSISDN": "03054517876",
        "AcquiredAfis": "test",
        "FingerNumber": "2",
        "ImageType": "4",
        "BioDeviceName": ""
    }
    acc_leg1_resp = requests.post(ACCOUNT_REG_URL, headers=dynamic_headers, json=acc_reg_payload_leg1)
    results["AccountRegistration_Leg1"] = safe_json(acc_leg1_resp)
    acc_tid = results["AccountRegistration_Leg1"].get("TransactionID") or results["AccountRegistration_Leg1"].get("transactionId")

    if acc_tid:
        # 3️⃣ ACCOUNT REGISTRATION - LEG 2
        acc_reg_payload_leg2 = acc_reg_payload_leg1.copy()
        acc_reg_payload_leg2["TransactionID"] = acc_tid
        acc_leg2_resp = requests.post(ACCOUNT_REG_URL, headers=dynamic_headers, json=acc_reg_payload_leg2)
        results["AccountRegistration_Leg2"] = safe_json(acc_leg2_resp)
        otp_code = results["AccountRegistration_Leg2"].get("OTP") or results["AccountRegistration_Leg2"].get("otp")

        if otp_code:
            # 4️⃣ ACCOUNT REGISTRATION - LEG 3
            acc_reg_payload_leg3 = acc_reg_payload_leg2.copy()
            acc_reg_payload_leg3["OTP"] = otp_code
            acc_leg3_resp = requests.post(ACCOUNT_REG_URL, headers=dynamic_headers, json=acc_reg_payload_leg3)
            results["AccountRegistration_Leg3"] = safe_json(acc_leg3_resp)

    # 5️⃣ CASH DEPOSIT INQUIRY
    cd_payload = {
        "DepositAmount": "100",
        "Longitude": "31.5686808",
        "Latitude": "74.3000874",
        "CustomerCNIC": "3740577357058",
        "CustomerMSISDN": "923376246667"
    }
    cd_resp = requests.post(CASH_DEPOSIT_URL, headers=dynamic_headers, json=cd_payload)
    results["CashDeposit"] = safe_json(cd_resp)
    cd_tid = results["CashDeposit"].get("TransactionID") or results["CashDeposit"].get("transactionId")
    if cd_tid:
        # 6️⃣ CASH DEPOSIT CONFIRMATION (hit twice)
        cd_confirm_payload = {
            "TransactionID": cd_tid,
            "TermsAccepted": "true",
            "DepositAmount": "100",
            "Longitude": "31.5686808",
            "Latitude": "74.3000874",
            "CustomerMSISDN": "923376246667",
            "AcquiredAfis": "test",
            "BioDeviceName": "test",
            "FingerNumber": "1",
            "ImageType": "4",
            "MPOS": "1111@923355923388"
        }
        results["CashDepositConfirmation_1"] = safe_json(
            requests.post(CASH_DEPOSIT_CONFIRM_URL, headers=dynamic_headers, json=cd_confirm_payload)
        )
        results["CashDepositConfirmation_2"] = safe_json(
            requests.post(CASH_DEPOSIT_CONFIRM_URL, headers=dynamic_headers, json=cd_confirm_payload)
        )

    # 7️⃣ CASH WITHDRAWAL INQUIRY
    cw_payload = {
        "WithdrawalAmount": "500",
        "Longitude": "31.5686808",
        "Latitude": "74.3000874",
        "CustomerCNIC": "3740577357058",
        "CustomerMSISDN": "923376246667"
    }
    cw_resp = requests.post(CASH_WITHDRAWAL_URL, headers=dynamic_headers, json=cw_payload)
    results["CashWithdrawal"] = safe_json(cw_resp)
    cw_tid = results["CashWithdrawal"].get("TransactionID") or results["CashWithdrawal"].get("transactionId")
    if cw_tid:
        # 8️⃣ CASH WITHDRAWAL CONFIRMATION
        cw_confirm_payload = {
            "TransactionID": cw_tid,
            "TermsAccepted": "true",
            "WithdrawalAmount": "500",
            "Longitude": "31.5686808",
            "Latitude": "74.3000874",
            "CustomerMSISDN": "923376246667",
            "AcquiredAfis": "test",
            "BioDeviceName": "test",
            "FingerNumber": "1",
            "ImageType": "4",
            "MPOS": "1111@923355923388"
        }
        results["CashWithdrawalConfirmation"] = safe_json(
            requests.post(CASH_WITHDRAWAL_CONFIRM_URL, headers=dynamic_headers, json=cw_confirm_payload)
        )

    # 9️⃣ CNIC TO MA INQUIRY
    ctm_payload = {
        "TransactionID": "0",
        "ReceiverAccountNumber": "923345768675",
        "DepositAmount": "1200",
        "Longitude": "173.433",
        "Latitude": "183.1222",
        "Serial Number": "123",
        "AquiredAfis": "abcxyz",
        "FingerNumber": "2",
        "ImageType": "4",
        "BioDeviceName": "Abc",
        "DepositReason": "Others",
        "SenderCNIC": "3759574626262",
        "SenderMSISDN": "923345643838"
    }
    ctm_resp = requests.post(CNIC_TO_MA_URL, headers=dynamic_headers, json=ctm_payload)
    results["CNICtoMA"] = safe_json(ctm_resp)
    ctm_tid = results["CNICtoMA"].get("TransactionID") or results["CNICtoMA"].get("transactionId")
    if ctm_tid:
        # 🔟 CNIC TO MA CONFIRMATION (hit twice)
        ctmc_payload = {
            "ReceiverAccountNumber": "923345876677",
            "TransactionID": ctm_tid,
            "TermsAccepted": "true",
            "DepositAmount": "100",
            "DepositReason": "Education",
            "Longitude": "31.5686808",
            "Latitude": "74.3000874",
            "SenderMSISDN": "923376246667",
            "SenderCNIC": "3740577357007",
            "AcquiredAfis": "test",
            "BioDeviceName": "test",
            "FingerNumber": "1",
            "MPOS": "1233@923457685757",
            "ImageType": "4"
        }
        results["CNICtoMAConfirmation_1"] = safe_json(
            requests.post(CNIC_TO_MA_CONFIRM_URL, headers=dynamic_headers, json=ctmc_payload)
        )
        results["CNICtoMAConfirmation_2"] = safe_json(
            requests.post(CNIC_TO_MA_CONFIRM_URL, headers=dynamic_headers, json=ctmc_payload)
        )

    return jsonify(results)


def safe_json(response):
    try:
        return response.json()
    except Exception:
        return {"raw_response": response.text, "status": response.status_code}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=True)