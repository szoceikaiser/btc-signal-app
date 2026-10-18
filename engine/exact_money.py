"""Exact decimal-input money for the offline spot book, budget-v2.

Inputs mean their finite decimal spelling (str(float)), not binary expansions.
Fractions keep all decimal products exact, with no context precision or cutoff.
BTC and execution quotes remain IEEE floats at the declared conversion boundary.
"""
from fractions import Fraction
import math


def decimal(value):
    if isinstance(value, Fraction):
        return value
    if not math.isfinite(float(value)):
        raise ValueError('Non-finite monetary input')
    return Fraction(str(value))


class Money:
    def __eq__(self, other):
        return isinstance(other, Money) and self.__dict__ == other.__dict__

    def __init__(self, capital):
        self.initial = self.cash = decimal(capital)
        self.alloc = self.spent = self.proceeds = self.fees = Fraction(0)
        self.quantity_rounding = Fraction(0)
        self.pending = {}
        if self.cash < 0:
            raise ValueError('Negative capital')

    @property
    def reserved(self):
        return sum(self.pending.values(), Fraction(0))

    @property
    def available(self):
        return self.cash - self.reserved

    def request(self, pct):
        value = self.alloc * decimal(pct) / 100
        if value < 0:
            raise ValueError('Negative budget share')
        return value

    def reserve(self, ident, amount):
        if ident in self.pending or not 0 < amount <= self.available:
            raise ValueError('Invalid exact reservation')
        self.pending[ident] = amount

    def amount(self, order):
        amount = self.pending.get(order['id'])
        if (amount is None or order.get('amount_exact') != str(amount)
                or order['amount'] != float(amount)
                or 'requested_exact' not in order
                or Fraction(order['requested_exact']) != self.request(order['tranche_pct'])
                or order['requested'] != float(Fraction(order['requested_exact']))):
            raise ValueError('Missing or inconsistent exact pending budget')
        return amount

    def release(self, order):
        amount = self.amount(order)
        del self.pending[order['id']]
        return amount

    def buy(self, order, fee, quantity, price):
        amount = self.release(order)
        charge = amount * decimal(fee)
        self.cash -= amount
        self.spent += amount
        self.fees += charge
        residual = amount - charge - decimal(quantity) * decimal(price)
        self.quantity_rounding += residual
        return charge, residual

    def sell(self, quantity, price, fee):
        gross = decimal(quantity) * decimal(price)
        charge = gross * decimal(fee)
        net = gross - charge
        self.cash += net
        self.proceeds += net
        self.fees += charge
        return charge, net

    def state(self):
        return {k: {i: str(a) for i, a in v.items()} if k == 'pending' else str(v)
                for k, v in self.__dict__.items()}

    @classmethod
    def restore(cls, state):
        obj = cls(0)
        if set(state) != set(obj.__dict__):
            raise ValueError('Incomplete exact money history')
        try:
            for k, value in state.items():
                setattr(obj, k, {i: Fraction(a) for i, a in value.items()} if k == 'pending' else Fraction(value))
            assert obj.cash == obj.initial + obj.proceeds - obj.spent
            assert all(getattr(obj, k) >= 0 for k in ('initial','cash','alloc','spent','proceeds','fees'))
            assert all(a > 0 for a in obj.pending.values()) and obj.available >= 0
            assert obj.state() == state  # canonical, complete serialization
        except (ValueError, TypeError, ZeroDivisionError, AssertionError) as exc:
            raise ValueError('Invalid exact money history') from exc
        return obj
