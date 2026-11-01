"""
Web Flask
"""

import os
import re
import secrets
from datetime import timedelta
from functools import wraps
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for


