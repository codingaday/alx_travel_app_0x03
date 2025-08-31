
import json
import logging
import re
import uuid
from decimal import Decimal
from typing import Dict, Optional, Tuple

import requests
from django.conf import settings

logger = logging.getLogger("Chapa Service")


class ChapaAPIError(Exception):
    """Custom exception for Chapa API errors"""

    pass


class ChapaService:
    """Service class for interacting with Chapa Payment API"""

    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.base_url = settings.CHAPA_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def generate_reference(self) -> str:
        """Generate unique payment reference"""
        return f"ALX_TRAVEL_{uuid.uuid4().hex[:8].upper()}"

    def _validate_email(self, email: str) -> str:
        """
        Validate and clean email address for Chapa API

        Args:
            email: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValueError: If email is invalid
        """
        if not email or not email.strip():
            raise ValueError("Email address is required")

        email = email.strip().lower()

        # Basic email pattern validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    def _clean_name(self, name: str, field_name: str = "name") -> str:
        """
        Clean and validate name fields for Chapa API

        Args:
            name: Name to clean
            field_name: Field name for error messages

        Returns:
            Cleaned name
        """
        if not name or not name.strip():
            # Return a default name if empty
            return "Customer"

        # Remove extra whitespace and special characters
        cleaned_name = re.sub(r"[^\w\s-]", "", name.strip())
        cleaned_name = " ".join(cleaned_name.split())  # Remove multiple spaces

        if not cleaned_name:
            return "Customer"

        # Chapa might have length restrictions
        if len(cleaned_name) > 50:
            cleaned_name = cleaned_name[:50].strip()

        return cleaned_name

    def _clean_phone(self, phone: str) -> str:
        """
        Clean and validate phone number for Chapa API
        Based on Chapa documentation: 09xxxxxxxx or 07xxxxxxxx format

        Args:
            phone: Phone number to clean

        Returns:
            Cleaned phone number in Ethiopian format
        """
        if not phone:
            return ""

        # Remove all non-digit characters
        cleaned_phone = re.sub(r"\D", "", phone.strip())

        # Handle Ethiopian phone numbers according to Chapa requirements
        if cleaned_phone.startswith("251"):
            # Remove country code to get local format
            local_part = cleaned_phone[3:]
            if len(local_part) == 9:
                # Convert to 10-digit format with leading 0
                if local_part.startswith("9"):
                    return f"0{local_part}"
                elif local_part.startswith("7"):
                    return f"0{local_part}"
        elif cleaned_phone.startswith("0") and len(cleaned_phone) == 10:
            # Already in correct format (09xxxxxxxx or 07xxxxxxxx)
            if cleaned_phone.startswith("09") or cleaned_phone.startswith("07"):
                return cleaned_phone
        elif len(cleaned_phone) == 9:
            # Add leading 0 if it starts with 9 or 7
            if cleaned_phone.startswith("9") or cleaned_phone.startswith("7"):
                return f"0{cleaned_phone}"

        # If we can't format it properly, return empty string
        # Chapa says phone is not required
        return ""

    def initiate_payment(
        self,
        amount: Decimal,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str = "",
        tx_ref: str = None,
        callback_url: str = None,
        return_url: str = None,
        description: str = "Travel Booking Payment",
    ) -> Tuple[bool, Dict]:
        """
        Initiate payment with Chapa API

        Args:
            amount: Payment amount
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Customer phone (optional)
            tx_ref: Transaction reference (auto-generated if not provided)
            callback_url: Webhook callback URL
            return_url: Return URL after payment
            description: Payment description

        Returns:
            Tuple of (success: bool, response_data: dict)
        """

        try:
            # Validate and clean input data
            validated_email = self._validate_email(email)
            cleaned_first_name = self._clean_name(first_name, "first_name")
            cleaned_last_name = self._clean_name(last_name, "last_name")
            cleaned_phone = self._clean_phone(phone_number)

            # Ensure we have valid names
            if cleaned_first_name == "Customer" and cleaned_last_name == "Customer":
                # Split email username as fallback
                email_username = validated_email.split("@")[0]
                if "_" in email_username or "." in email_username:
                    parts = re.split(r"[._]", email_username)
                    if len(parts) >= 2:
                        cleaned_first_name = parts[0].capitalize()
                        cleaned_last_name = parts[1].capitalize()
                else:
                    cleaned_first_name = email_username.capitalize()
                    cleaned_last_name = "User"

            if not tx_ref:
                tx_ref = self.generate_reference()

            # Build payload with validated data
            payload = {
                "amount": str(amount),
                "currency": "ETB",
                "email": validated_email,
                "first_name": cleaned_first_name,
                "last_name": cleaned_last_name,
                "tx_ref": tx_ref,
                "description": description[:100],  # Ensure description isn't too long
                "meta": {
                    "title": description[:50],
                    "source": "ALX Travel App",
                },
            }

            # Add optional fields only if they have values
            if cleaned_phone:
                payload["phone_number"] = cleaned_phone
            if callback_url:
                payload["callback_url"] = callback_url
            if return_url:
                payload["return_url"] = return_url

            logger.info(f"Initiating Chapa payment with validated data: {tx_ref}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.base_url}/transaction/initialize",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            logger.info(f"Chapa API response status: {response.status_code}")

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from Chapa: {response.text}")
                return False, {"error": "Invalid response from payment provider"}

            logger.debug(f"Chapa API response: {json.dumps(response_data, indent=2)}")

            if response.status_code == 200 and response_data.get("status") == "success":
                logger.info(f"Payment initiated successfully: {tx_ref}")
                return True, response_data
            else:
                error_msg = response_data.get("message", "Unknown error")
                error_details = response_data.get("errors", {})

                logger.error(f"Payment initiation failed: {tx_ref} - {error_msg}")
                if error_details:
                    logger.error(f"Error details: {error_details}")

                return False, {
                    "error": error_msg,
                    "details": error_details,
                    "status_code": response.status_code,
                }

        except ValueError as e:
            logger.error(f"Validation error during payment initiation: {str(e)}")
            return False, {"error": f"Validation error: {str(e)}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment initiation: {str(e)}")
            return False, {"error": "Network error occurred"}
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            return False, {"error": "An unexpected error occurred"}

    def verify_payment(self, tx_ref: str) -> Tuple[bool, Dict]:
        """
        Verify payment status with Chapa API

        Args:
            tx_ref: Transaction reference to verify

        Returns:
            Tuple of (success: bool, response_data: dict)
        """

        try:
            response = requests.get(
                f"{self.base_url}/transaction/verify/{tx_ref}",
                headers=self.headers,
                timeout=30,
            )

            logger.info(f"Verifying payment: {tx_ref}")

            response_data = response.json()

            if response.status_code == 200:
                payment_status = response_data.get("status")
                if payment_status == "success":
                    data = response_data.get("data", {})
                    chapa_status = data.get("status", "").lower()

                    if chapa_status == "success":
                        logger.info(f"Payment verified successfully: {tx_ref}")
                        return True, response_data
                    else:
                        logger.warning(
                            f"Payment verification failed: {tx_ref} - Status: {chapa_status}"
                        )
                        return False, response_data
                else:
                    logger.error(f"Payment verification request failed: {tx_ref}")
                    return False, response_data
            else:
                logger.error(
                    f"HTTP error during payment verification: {response.status_code}"
                )
                return False, response_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return False, {"error": "Network error occurred"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Chapa: {str(e)}")
            return False, {"error": "Invalid response from payment provider"}
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return False, {"error": "An unexpected error occurred"}

    def get_payment_status(self, tx_ref: str) -> Optional[str]:
        """
        Get simplified payment status

        Args:
            tx_ref: Transaction reference

        Returns:
            Payment status string or None if verification failed
        """
        success, data = self.verify_payment(tx_ref)

        if success:
            payment_data = data.get("data", {})
            chapa_status = payment_data.get("status", "").lower()

            # Map Chapa status to our internal status
            status_mapping = {
                "success": "completed",
                "pending": "processing",
                "failed": "failed",
                "cancelled": "cancelled",
            }

            return status_mapping.get(chapa_status, "pending")

        return None
        if not re.match(email_pattern, email):
            raise ValueError(f"Invalid email format: {email}")

        # Chapa might not accept certain domains - let's avoid common test domains
        blocked_domains = ["example.com", "test.com", "fake.com", "dummy.com"]
        domain = email.split("@")[1] if "@" in email else ""

        if domain in blocked_domains:
            raise ValueError(
                f"Email domain '{domain}' not accepted by payment provider"
            )

        # Additional Chapa-specific validations
        if len(email) > 100:  # Reasonable email length limit
            raise ValueError("Email address too long")

        if ".." in email:  # No consecutive dots
            raise ValueError("Email contains consecutive dots")

        if email.startswith(".") or email.endswith("."):  # No leading/trailing dots
            raise ValueError("Email cannot start or end with a dot")

        return email

    def _clean_name(self, name: str, field_name: str = "name") -> str:
        """
        Clean and validate name fields for Chapa API

        Args:
            name: Name to clean
            field_name: Field name for error messages

        Returns:
            Cleaned name
        """
        if not name or not name.strip():
            # Return a default name if empty
            return "Customer"

        # Remove extra whitespace and special characters
        cleaned_name = re.sub(r"[^\w\s-]", "", name.strip())
        cleaned_name = " ".join(cleaned_name.split())  # Remove multiple spaces

        if not cleaned_name:
            return "Customer"

        # Chapa might have length restrictions
        if len(cleaned_name) > 50:
            cleaned_name = cleaned_name[:50].strip()

        return cleaned_name

    def _clean_phone(self, phone: str) -> str:
        """
        Clean and validate phone number for Chapa API

        Args:
            phone: Phone number to clean

        Returns:
            Cleaned phone number
        """
        if not phone:
            return ""

        # Remove all non-digit characters
        cleaned_phone = re.sub(r"\D", "", phone.strip())

        # Handle Ethiopian phone numbers
        if cleaned_phone.startswith("251"):
            # Already has country code
            return f"+{cleaned_phone}"
        elif cleaned_phone.startswith("0") and len(cleaned_phone) == 10:
            # Local Ethiopian number starting with 0
            return f"+251{cleaned_phone[1:]}"
        elif len(cleaned_phone) == 9:
            # Local Ethiopian number without leading 0
            return f"+251{cleaned_phone}"
        elif len(cleaned_phone) > 10:
            # Assume it already has country code
            return f"+{cleaned_phone}"

        return cleaned_phone if cleaned_phone else ""

    def initiate_payment(
        self,
        amount: Decimal,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str = "",
        tx_ref: str = None,
        callback_url: str = None,
        return_url: str = None,
        description: str = "Travel Booking Payment",
    ) -> Tuple[bool, Dict]:
        """
        Initiate payment with Chapa API

        Args:
            amount: Payment amount
            email: Customer email
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Customer phone (optional)
            tx_ref: Transaction reference (auto-generated if not provided)
            callback_url: Webhook callback URL
            return_url: Return URL after payment
            description: Payment description

        Returns:
            Tuple of (success: bool, response_data: dict)
        """

        try:
            # Validate and clean input data
            validated_email = self._validate_email(email)
            cleaned_first_name = self._clean_name(first_name, "first_name")
            cleaned_last_name = self._clean_name(last_name, "last_name")
            cleaned_phone = self._clean_phone(phone_number)

            # Ensure we have valid names
            if cleaned_first_name == "Customer" and cleaned_last_name == "Customer":
                # Split email username as fallback
                email_username = validated_email.split("@")[0]
                if "_" in email_username or "." in email_username:
                    parts = re.split(r"[._]", email_username)
                    if len(parts) >= 2:
                        cleaned_first_name = parts[0].capitalize()
                        cleaned_last_name = parts[1].capitalize()
                else:
                    cleaned_first_name = email_username.capitalize()
                    cleaned_last_name = "User"

            if not tx_ref:
                tx_ref = self.generate_reference()

            # Build payload with validated data
            payload = {
                "amount": str(amount),
                "currency": "ETB",
                "email": validated_email,
                "first_name": cleaned_first_name,
                "last_name": cleaned_last_name,
                "tx_ref": tx_ref,
                "description": description[:100],  # Ensure description isn't too long
                "meta": {
                    "title": description[:50],
                    "source": "ALX Travel App",
                },
            }

            # Add optional fields only if they have values
            if cleaned_phone:
                payload["phone_number"] = cleaned_phone
            if callback_url:
                payload["callback_url"] = callback_url
            if return_url:
                payload["return_url"] = return_url

            logger.info(f"Initiating Chapa payment with validated data: {tx_ref}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                f"{self.base_url}/transaction/initialize",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            logger.info(f"Chapa API response status: {response.status_code}")

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response from Chapa: {response.text}")
                return False, {"error": "Invalid response from payment provider"}

            logger.debug(f"Chapa API response: {json.dumps(response_data, indent=2)}")

            if response.status_code == 200 and response_data.get("status") == "success":
                logger.info(f"Payment initiated successfully: {tx_ref}")
                return True, response_data
            else:
                error_msg = response_data.get("message", "Unknown error")
                error_details = response_data.get("errors", {})

                logger.error(f"Payment initiation failed: {tx_ref} - {error_msg}")
                if error_details:
                    logger.error(f"Error details: {error_details}")

                return False, {
                    "error": error_msg,
                    "details": error_details,
                    "status_code": response.status_code,
                }

        except ValueError as e:
            logger.error(f"Validation error during payment initiation: {str(e)}")
            return False, {"error": f"Validation error: {str(e)}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment initiation: {str(e)}")
            return False, {"error": "Network error occurred"}
        except Exception as e:
            logger.error(f"Unexpected error during payment initiation: {str(e)}")
            return False, {"error": "An unexpected error occurred"}

    def verify_payment(self, tx_ref: str) -> Tuple[bool, Dict]:
        """
        Verify payment status with Chapa API

        Args:
            tx_ref: Transaction reference to verify

        Returns:
            Tuple of (success: bool, response_data: dict)
        """

        try:
            response = requests.get(
                f"{self.base_url}/transaction/verify/{tx_ref}",
                headers=self.headers,
                timeout=30,
            )

            logger.info(f"Verifying payment: {tx_ref}")

            response_data = response.json()

            if response.status_code == 200:
                payment_status = response_data.get("status")
                if payment_status == "success":
                    data = response_data.get("data", {})
                    chapa_status = data.get("status", "").lower()

                    if chapa_status == "success":
                        logger.info(f"Payment verified successfully: {tx_ref}")
                        return True, response_data
                    else:
                        logger.warning(
                            f"Payment verification failed: {tx_ref} - Status: {chapa_status}"
                        )
                        return False, response_data
                else:
                    logger.error(f"Payment verification request failed: {tx_ref}")
                    return False, response_data
            else:
                logger.error(
                    f"HTTP error during payment verification: {response.status_code}"
                )
                return False, response_data

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during payment verification: {str(e)}")
            return False, {"error": "Network error occurred"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Chapa: {str(e)}")
            return False, {"error": "Invalid response from payment provider"}
        except Exception as e:
            logger.error(f"Unexpected error during payment verification: {str(e)}")
            return False, {"error": "An unexpected error occurred"}

    def get_payment_status(self, tx_ref: str) -> Optional[str]:
        """
        Get simplified payment status

        Args:
            tx_ref: Transaction reference

        Returns:
            Payment status string or None if verification failed
        """
        success, data = self.verify_payment(tx_ref)

        if success:
            payment_data = data.get("data", {})
            chapa_status = payment_data.get("status", "").lower()

            # Map Chapa status to our internal status
            status_mapping = {
                "success": "completed",
                "pending": "processing",
                "failed": "failed",
                "cancelled": "cancelled",
            }

            return status_mapping.get(chapa_status, "pending")

        return None
