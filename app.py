import requests
import io
import base64
import logging
from typing import Tuple
from datetime import datetime

from PIL import Image
from captcha_decoder import solve_captcha
from bot import send_message_tele, send_message_disc

url = "https://booking.bbdc.sg/bbdc-back-service/api/"
LoginCaptcha_url = "/auth/getLoginCaptchaImage"
Login_url = "auth/login"
jsessionid_url = "account/listAccountCourseType"
AvailableSlots_url = "booking/c3practical/listC3PracticalSlotReleased"
BookingCaptcha_url = "booking/manage/getCaptchaImage"
Booking_url = "booking/c3practical/callBookC3PracticalSlot"

# setup logging
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


def PostUrl(url, headers, payload):
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    return data


def base64img(encoded_data):
    fh = io.BytesIO()
    fh.write(base64.b64decode(encoded_data))
    fh.flush()
    return fh


class Api:
    @staticmethod
    def get_captcha_image(extension: str, headers: dict):
        data = PostUrl(
            url + (LoginCaptcha_url if extension == "Login" else BookingCaptcha_url),
            headers,
            None,
        )
        if data["data"]:
            data["data"].pop("accountIdNric")
        return data

    # get jsessionid
    @staticmethod
    def get_jsessionid(bearerToken: str) -> str:
        headers = {"authorization": bearerToken}
        data = PostUrl(url + jsessionid_url, headers, None)
        if data["success"]:
            jsessionid = data["data"]["activeCourseList"][0]["authToken"]
            courseType = data["data"]["activeCourseList"][0]["courseType"]
            return jsessionid, courseType

    # get slots
    @staticmethod
    def get_slots(headers: dict, courseType: str, releasedSlotMonth: str) -> dict:
        AvailableSlotsPayload = {
            "courseType": courseType,
            "releasedSlotMonth": releasedSlotMonth,
            "stageSubDesc": "Practical Lesson",
            "subVehicleType": None,
            "subStageSubNo": None,
        }
        data = PostUrl(url + AvailableSlots_url, headers, AvailableSlotsPayload)
        if data["success"]:
            slots = data["data"]["releasedSlotListGroupByDay"]
            return slots

    # get login bearer token
    @staticmethod
    def login(username: str, password: str, captcha: str, captchaResponse: dict) -> str:
        data = {
            "userId": username,
            "userPass": password,
            "verifyCodeValue": captcha,
        }
        data.update(captchaResponse["data"])
        # print(data)
        loginData = PostUrl(url + Login_url, None, data)
        return loginData

    # book slot
    def book(headers: dict, captcha: str, captchaResponse: dict, slotPayload: dict):
        data = {"verifyCodeValue": captcha}
        data.update(captchaResponse["data"])
        data.update(slotPayload)
        bookingData = PostUrl(url + Booking_url, headers, data)
        return bookingData


class Session:
    bearerToken: str = None
    jsessionid: str
    courseType: str
    slots: dict

    def __init__(self):
        pass

    def __get_auth_header(self):
        return {"authorization": self.bearerToken, "jsessionid": self.jsessionid}

    @staticmethod
    def __process_captcha_response(data) -> Tuple[str, int]:
        data = data["data"]
        encoded_data = data.pop("image").split(",")[1]
        return solve_captcha(base64img(encoded_data))

    @staticmethod
    def __validate_captcha(Captcha: Tuple[str, int]) -> bool:
        (CaptchaData, CaptchaConfidence) = Captcha
        return len(CaptchaData) == 4 and CaptchaConfidence > 70

    # get best captcha
    def get_best_captcha(self, extension: str, headers: dict = None):
        captchaResponse = None
        captcha = None
        while captcha is None or not Session.__validate_captcha(captcha):
            captchaResponse = Api.get_captcha_image(extension, headers)
            captcha = Session.__process_captcha_response(captchaResponse)
        return (captcha[0], captchaResponse)

    def login(self, username: str, password: str, manual: bool):
        # retry login flow until captcha guessed is correct
        while True:
            if manual:
                captchaResponse = Api.get_captcha_image("Login", None)
                encoded_data = captchaResponse["data"].pop("image").split(",")[1]
                captchaImage = Image.open(base64img(encoded_data)).convert("RGB")
                captchaImage.show()
                captcha = input("Solve Login Captcha: ")
            else:
                (captcha, captchaResponse) = self.get_best_captcha("Login")
            loginData = Api.login(username, password, captcha, captchaResponse)
            if loginData["success"]:
                logging.info("Logged In")
                self.bearerToken = loginData["data"]["tokenContent"]
                self.jsessionid, self.courseType = Api.get_jsessionid(self.bearerToken)
                # print(self.bearerToken)
                break

    def manual_login(self, bearerToken: str):
        self.bearerToken = bearerToken
        self.jsessionid, self.courseType = Api.get_jsessionid(self.bearerToken)

    def is_expired(self):
        return not bool([Api.get_jsessionid(self.bearerToken)][0])

    # Get all slots in specific month
    def get_slots(self, releasedSlotMonth: str) -> dict:
        self.slots = Api.get_slots(
            self.__get_auth_header(), self.courseType, releasedSlotMonth
        )

    def display_slot(self, slot):
        slotDate = (
            datetime.strptime(slot["slotRefDate"], "%Y-%m-%d %H:%M:%S")
        ).strftime("%d/%m/%Y")
        message = """
        Slot Available
        Date: {}
        Time: {} - {}
        Session: {}
        Total Fee: {}""".format(
            slotDate,
            slot["startTime"],
            slot["endTime"],
            slot["slotRefName"],
            slot["totalFee"],
        )
        return message

    # Get slot payload for booking
    def get_slot_payload(self, slot):
        if slot:
            slotDict = {}
            slotDict["slotIdEnc"] = slot["slotIdEnc"]
            slotDict["bookingProgressEnc"] = slot["bookingProgressEnc"]
            slotPayload = {
                "courseType": self.courseType,
                "slotIdList": [slot["slotId"]],
                "encryptSlotList": [slotDict],
                "insInstructorId": "",
                "subVehicleType": None,
                "instructorType": "",
            }
            return slotPayload
        else:
            logging.info("No Slot Available")

    # Get preferred slot in month if possible else get earliest date
    def choose_slot(self, want: list = None):
        if self.slots:
            # Sorting
            keylist = list(self.slots.keys())
            keylist.sort()
            earliestDate = keylist[0]
            chosenSlot = self.slots[earliestDate][0]
            if want:
                for slot in self.slots[earliestDate]:
                    if int(slot["slotRefName"].split()[1]) in want:
                        chosenSlot = slot
                        break

            # Payload for booking
            return chosenSlot

    # Book using slot payload
    def book(self, slotPayload: dict, manual: bool):
        headers = self.__get_auth_header()
        if slotPayload:
            while True:
                if manual:
                    captchaResponse = Api.get_captcha_image("Booking", headers)
                    encoded_data = captchaResponse["data"].pop("image").split(",")[1]
                    captchaImage = Image.open(base64img(encoded_data)).convert("RGB")
                    captchaImage.show()
                    captcha = input("Solve Booking Captcha: ")
                    if captcha == "n":
                        logging.info("Ignoring this slot...")
                        break
                else:
                    (captcha, captchaResponse) = self.get_best_captcha(
                        "Booking", headers
                    )
                bookingData = Api.book(headers, captcha, captchaResponse, slotPayload)
                if bookingData["success"]:
                    bookedSlot = bookingData["data"]["bookedPracticalSlotList"][0]
                    logging.info(bookedSlot["message"])
                    break


def app(session, config):
    # Login
    userId = config["login"]["username"]
    userPass = config["login"]["password"]

    # Preferred Month and Slot
    month = config["pref"]["month"]
    want = config["pref"]["sessions"]

    # Manually Solve Captchas
    manualL = config["captcha"]["login"]
    manualB = config["captcha"]["booking"]

    # Telegram Bot
    bot_token = config["telegram"]["token"]
    chat_id = config["telegram"]["chat_id"]
    enable_tele = config["telegram"]["enabled"]

    # Discord Bot
    enable_disc = config["discord"]["enabled"]
    webhook = config["discord"]["webhook"]

    enable_booking = config["enable_booking"]

    # Attempt Login
    if session.is_expired():
        logging.info("Attempting to login...")
        session.login(userId, userPass, manualL)
        # session.manual_login(bearerToken)

    # Get Slot
    session.get_slots(month)
    chosenSlot = session.choose_slot(want)
    slotPayload = session.get_slot_payload(chosenSlot)

    # Attempt Booking
    if slotPayload:
        message = session.display_slot(chosenSlot)
        logging.info(message)
        if enable_tele:
            send_message_tele(message, bot_token, chat_id)
        if enable_disc:
            send_message_disc(message, webhook)
        if enable_booking:
            logging.info("Attempting to book...")
            session.book(slotPayload, manualB)
