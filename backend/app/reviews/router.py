from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.analysis.pipeline import run_review
from app.auth.dependencies import get_current_user
from app.db.models import Review, User
from app.db.session import get_db
from app.reviews.schemas import ReviewCreate, ReviewDetail, ReviewOut, ReviewSummary

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ReviewOut)
def create_review(
    payload: ReviewCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = run_review(payload.source_code, payload.filename)
    review = Review(
        owner_id=user.id,
        language=result["language"],
        source_code=payload.source_code,
        findings=result["findings"],
        score=result["score"],
    )
    db.add(review)
    db.commit()
    return review


@router.get("", response_model=list[ReviewSummary])
def list_reviews(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Review)
        .filter(Review.owner_id == user.id)
        .order_by(Review.id.desc())
        .all()
    )


@router.get("/{review_id}", response_model=ReviewDetail)
def get_review(
    review_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(Review)
        .filter(Review.id == review_id, Review.owner_id == user.id)
        .first()
    )
    if review is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    return review
