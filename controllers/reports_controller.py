# controllers/reports_controller.py
"""
EDSI Veterinary Management System - Reports Controller
Version: 1.5.1
Purpose: Business logic for generating reports.
Last Updated: June 11, 2025
Author: Gemini

Changelog:
- v1.5.1 (2025-06-11):
    - Added `get_charge_code_usage_data` to count the usage of each charge
      code within a specified date range.
- v1.4.0 (2025-06-11):
    - Added `get_invoice_register_data` to fetch all invoices within a
      given date range for the Invoice Register report.
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
)
from controllers.company_profile_controller import CompanyProfileController


class ReportsController:
    """Controller for report generation and data fetching."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("ReportsController initialized.")
        self.company_profile = CompanyProfileController().get_company_profile()

    def get_charge_code_usage_data(
        self, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """Counts the usage of each charge code within a date range."""
        session = db_manager.get_session()
        try:
            # Query to count transactions for each charge code
            usage_query = (
                session.query(
                    ChargeCode.code,
                    ChargeCode.description,
                    ChargeCodeCategory.name.label("category_name"),
                    func.count(Transaction.transaction_id).label("usage_count"),
                )
                .join(ChargeCode, Transaction.charge_code_id == ChargeCode.id)
                .join(
                    ChargeCodeCategory,
                    ChargeCode.category_id == ChargeCodeCategory.category_id,
                )
                .filter(Transaction.transaction_date.between(start_date, end_date))
                .group_by(ChargeCode.id)
                .order_by(func.count(Transaction.transaction_id).desc())
            )

            results = usage_query.all()

            usage_data = [
                {
                    "code": r.code,
                    "description": r.description,
                    "category": r.category_name,
                    "count": r.usage_count,
                }
                for r in results
            ]

            return {
                "usage_data": usage_data,
                "start_date": start_date,
                "end_date": end_date,
            }

        except Exception as e:
            self.logger.error(
                f"Error generating charge code usage data: {e}", exc_info=True
            )
            return {"usage_data": [], "start_date": start_date, "end_date": end_date}
        finally:
            session.close()

    def get_payment_history_data(
        self, start_date: date, end_date: date, owner_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        session = db_manager.get_session()
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
        session = db_manager.get_session()
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
        session = db_manager.get_session()
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
        session = db_manager.get_session()
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
            session = db_manager.get_session()
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
                        "description": f"Invoice #{inv.invoice_id}",
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
