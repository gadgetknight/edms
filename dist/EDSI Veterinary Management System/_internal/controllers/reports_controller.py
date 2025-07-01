# controllers/reports_controller.py

"""
EDSI Veterinary Management System - Reports Controller
Version: 1.7.2
Purpose: Business logic for generating reports.
Last Updated: June 28, 2025
Author: Gemini

Changelog:
- v1.7.2 (2025-06-28):
    - **BUG FIX**: Corrected `db_manager.get_session()` to `db_manager().get_session()`
      in `get_charge_code_usage_data`, `get_horse_transaction_history_data`,
      `get_payment_history_data`, `get_invoice_register_data`, `get_ar_aging_data`,
      and `get_data_for_all_owner_statements` to properly retrieve the `DatabaseManager`
      instance and resolve `AttributeError: 'function' object has no attribute 'get_session'`.
- v1.7.1 (2025-06-12):
    - Fixed an AttributeError in `get_charge_code_usage_data` by correcting the
      SQLAlchemy join condition for ChargeCodeCategory from the incorrect '.id'
      to the correct '.category_id' primary key.
- v1.7.0 (2025-06-12):
    - Upgraded `get_charge_code_usage_data` to be a full-featured method.
    - It now accepts an `options` dictionary to handle UI-driven sorting and grouping.
    - The query now calculates total revenue in addition to usage count.
    - The returned data structure is now richer, including summary, details, and options.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from config.database_config import db_manager
from models import (
    Owner,
    Invoice,
    OwnerPayment,
    OwnerBillingHistory,
    Transaction,
    ChargeCode,
    ChargeCodeCategory,
    Horse,
    User,
)
from controllers.company_profile_controller import CompanyProfileController


class ReportsController:
    """Controller for report generation and data fetching."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ReportsController initialized.")
        self.company_profile = CompanyProfileController().get_company_profile()

    def get_charge_code_usage_data(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches and processes data for the Charge Code Usage report.

        Args:
            options: A dictionary of user-selected options from the UI.

        Returns:
            A dictionary containing the processed data ready for the PDF generator.
        """
        session = db_manager().get_session()  # Corrected call
        try:
            start_date = options["start_date"]
            end_date = options["end_date"]

            # Base query to get usage count and revenue
            query = (
                session.query(
                    ChargeCode.code,
                    ChargeCode.description,
                    ChargeCodeCategory.name.label("category_name"),
                    func.count(Transaction.transaction_id).label("usage_count"),
                    func.sum(Transaction.total_price).label("total_revenue"),
                )
                .join(ChargeCode, Transaction.charge_code_id == ChargeCode.id)
                # MODIFIED: Corrected ChargeCodeCategory.id to ChargeCodeCategory.category_id
                .join(
                    ChargeCodeCategory,
                    ChargeCodeCategory.category_id == ChargeCode.category_id,
                )
                .filter(
                    and_(
                        Transaction.transaction_date >= start_date,
                        Transaction.transaction_date <= end_date,
                    )
                )
                .group_by(
                    ChargeCode.code, ChargeCode.description, ChargeCodeCategory.name
                )
            )

            results = query.all()

            if not results:
                return {"details": [], "summary": {}, "options": options}

            details = [
                {
                    "code": r.code,
                    "description": r.description,
                    "category_name": r.category_name,
                    "usage_count": r.usage_count,
                    "total_revenue": float(r.total_revenue) if r.total_revenue else 0.0,
                }
                for r in results
            ]

            # Sorting logic
            sort_by = options.get("sort_by", "Usage Count (High to Low)")
            reverse_sort = True
            sort_key = "usage_count"
            if sort_by == "Total Revenue (High to Low)":
                sort_key = "total_revenue"
            elif sort_by == "Charge Code (A-Z)":
                sort_key = "code"
                reverse_sort = False
            elif sort_by == "Category (A-Z)":
                sort_key = "category_name"
                reverse_sort = False

            details.sort(key=lambda x: x[sort_key], reverse=reverse_sort)

            summary = {
                "unique_codes_used": len(details),
                "total_usage_count": sum(item["usage_count"] for item in details),
                "total_revenue": sum(item["total_revenue"] for item in details),
            }

            return {
                "options": options,
                "summary": summary,
                "details": details,
            }

        except Exception as e:
            self.logger.error(
                f"Error fetching charge code usage data: {e}", exc_info=True
            )
            return {"error": str(e)}
        finally:
            session.close()

    def get_horse_transaction_history_data(
        self, horse_id: int, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Fetches all transactions for a single horse within a date range."""
        session = db_manager().get_session()  # Corrected call
        try:
            horse = session.query(Horse).filter(Horse.horse_id == horse_id).first()
            if not horse:
                return {
                    "error": "Horse not found",
                    "horse": None,
                    "transactions": [],
                    "start_date": start_date,
                    "end_date": end_date,
                }

            transactions = (
                session.query(Transaction)
                .filter(
                    Transaction.horse_id == horse_id,
                    Transaction.transaction_date.between(start_date, end_date),
                )
                .options(
                    joinedload(Transaction.charge_code),
                    joinedload(Transaction.administered_by),
                )
                .order_by(Transaction.transaction_date.asc())
                .all()
            )

            return {
                "horse": horse,
                "transactions": transactions,
                "start_date": start_date,
                "end_date": end_date,
            }
        except Exception as e:
            self.logger.error(
                f"Error generating horse transaction history for horse_id {horse_id}: {e}",
                exc_info=True,
            )
            return {
                "error": str(e),
                "horse": None,
                "transactions": [],
                "start_date": start_date,
                "end_date": end_date,
            }
        finally:
            session.close()

    def get_payment_history_data(
        self, start_date: date, end_date: date, owner_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        session = db_manager().get_session()  # Corrected call
        try:
            query = (
                session.query(OwnerPayment)
                .filter(OwnerPayment.payment_date.between(start_date, end_date))
                .options(joinedload(OwnerPayment.owner))
                .order_by(OwnerPayment.payment_date, OwnerPayment.owner_id)
            )
            if owner_id and owner_id != "all":
                query = query.filter(OwnerPayment.owner_id == owner_id)
            payments = query.all()
            return {
                "payments": payments,
                "start_date": start_date,
                "end_date": end_date,
            }
        except Exception as e:
            self.logger.error(
                f"Error generating payment history data: {e}", exc_info=True
            )
            return {"payments": [], "start_date": start_date, "end_date": end_date}
        finally:
            session.close()

    def get_invoice_register_data(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        session = db_manager().get_session()  # Corrected call
        try:
            invoices = (
                session.query(Invoice)
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .options(joinedload(Invoice.owner))
                .order_by(Invoice.invoice_date, Invoice.invoice_id)
                .all()
            )
            return {
                "invoices": invoices,
                "start_date": start_date,
                "end_date": end_date,
            }
        except Exception as e:
            self.logger.error(
                f"Error generating invoice register data: {e}", exc_info=True
            )
            return {"invoices": [], "start_date": start_date, "end_date": end_date}
        finally:
            session.close()

    def get_ar_aging_data(self, as_of_date: date) -> Dict[str, Any]:
        session = db_manager().get_session()  # Corrected call
        try:
            owners_with_balance = (
                session.query(Owner)
                .filter(Owner.is_active == True, Owner.balance > 0)
                .options(joinedload(Owner.invoices))
                .order_by(Owner.last_name)
                .all()
            )
            report_lines = []
            totals = {
                "current": Decimal("0.00"),
                "31-60": Decimal("0.00"),
                "61-90": Decimal("0.00"),
                "over_90": Decimal("0.00"),
                "total": Decimal("0.00"),
            }
            for owner in owners_with_balance:
                owner_buckets = {
                    "current": Decimal("0.00"),
                    "31-60": Decimal("0.00"),
                    "61-90": Decimal("0.00"),
                    "over_90": Decimal("0.00"),
                }
                unpaid_invoices = [inv for inv in owner.invoices if inv.balance_due > 0]
                for inv in unpaid_invoices:
                    age = (as_of_date - inv.invoice_date).days
                    if age <= 30:
                        owner_buckets["current"] += inv.balance_due
                    elif 31 <= age <= 60:
                        owner_buckets["31-60"] += inv.balance_due
                    elif 61 <= age <= 90:
                        owner_buckets["61-90"] += inv.balance_due
                    else:
                        owner_buckets["over_90"] += inv.balance_due
                owner_total = sum(owner_buckets.values())
                if owner_total > 0:
                    report_lines.append(
                        {
                            "name": owner.farm_name
                            or f"{owner.first_name or ''} {owner.last_name or ''}".strip(),
                            "buckets": owner_buckets,
                            "total": owner_total,
                        }
                    )
                    for key in totals:
                        if key != "total":
                            totals[key] += owner_buckets[key]
                totals["total"] += owner_total
            return {"lines": report_lines, "totals": totals, "as_of_date": as_of_date}
        except Exception as e:
            self.logger.error(f"Error generating A/R aging data: {e}", exc_info=True)
            return {"lines": [], "totals": {}, "as_of_date": as_of_date}
        finally:
            session.close()

    def get_data_for_all_owner_statements(
        self, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        session = db_manager().get_session()  # Corrected call
        try:
            owners_with_invoices = (
                session.query(Invoice.owner_id)
                .filter(Invoice.invoice_date.between(start_date, end_date))
                .distinct()
            )
            owners_with_payments = (
                session.query(OwnerPayment.owner_id)
                .filter(OwnerPayment.payment_date.between(start_date, end_date))
                .distinct()
            )
            owners_with_balance = (
                session.query(Owner.owner_id)
                .filter(Owner.is_active == True, Owner.balance != Decimal("0.00"))
                .distinct()
            )
            owner_ids = {r[0] for r in owners_with_invoices}
            owner_ids.update(r[0] for r in owners_with_payments)
            owner_ids.update(r[0] for r in owners_with_balance)
            all_statements_data = [
                s_data
                for owner_id in owner_ids
                if (
                    s_data := self.get_owner_statement_data(
                        owner_id, start_date, end_date, session
                    )
                )
            ]
            return all_statements_data
        except Exception as e:
            self.logger.error(
                f"Error gathering data for all owner statements: {e}", exc_info=True
            )
            return []
        finally:
            session.close()

    def get_owner_statement_data(
        self,
        owner_id: int,
        start_date: date,
        end_date: date,
        session: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        close_session = False
        if session is None:
            session = db_manager().get_session()  # Corrected call
            close_session = True
        try:
            owner = session.query(Owner).filter(Owner.owner_id == owner_id).first()
            if not owner:
                return None
            last_history = (
                session.query(OwnerBillingHistory)
                .filter(
                    OwnerBillingHistory.owner_id == owner_id,
                    OwnerBillingHistory.entry_date < start_date,
                )
                .order_by(OwnerBillingHistory.entry_date.desc())
                .first()
            )
            starting_balance = (
                last_history.new_balance if last_history else Decimal("0.00")
            )
            invoices = (
                session.query(Invoice)
                .filter(
                    Invoice.owner_id == owner_id,
                    Invoice.invoice_date.between(start_date, end_date),
                )
                .all()
            )
            payments = (
                session.query(OwnerPayment)
                .filter(
                    OwnerPayment.owner_id == owner_id,
                    OwnerPayment.payment_date.between(start_date, end_date),
                )
                .all()
            )
            statement_items = []
            for inv in invoices:
                statement_items.append(
                    {
                        "date": inv.invoice_date,
                        "type": "Invoice",
                        "description": f"Invoice #{inv.display_invoice_id}",  # Using the new display ID
                        "charge": inv.grand_total,
                        "payment": Decimal("0.00"),
                    }
                )
            for pmt in payments:
                ref = f" (Ref: {pmt.reference_number})" if pmt.reference_number else ""
                statement_items.append(
                    {
                        "date": pmt.payment_date,
                        "type": "Payment",
                        "description": f"Payment - {pmt.payment_method}{ref}",
                        "charge": Decimal("0.00"),
                        "payment": pmt.amount,
                    }
                )
            statement_items.sort(key=lambda x: x["date"])
            return {
                "owner": owner,
                "start_date": start_date,
                "end_date": end_date,
                "starting_balance": starting_balance,
                "items": statement_items,
            }
        except Exception as e:
            self.logger.error(
                f"Error generating owner statement data for owner ID {owner_id}: {e}",
                exc_info=True,
            )
            return None
        finally:
            if close_session:
                session.close()
