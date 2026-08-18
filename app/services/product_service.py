from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import Inventory
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.category import CategoryCreate

class ProductService:
    """
    Manages categories and products lifecycle.
    Good interview points:
    1. Paginated, searchable, filterable product retrieval using ORM query construction.
    2. Auto-creation of matching Inventory record on Product insert.
    """

    # --- CATEGORY SERVICES ---
    @staticmethod
    def create_category(db: Session, category_data: CategoryCreate) -> Category:
        existing = db.query(Category).filter(Category.name == category_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this name already exists."
            )
        category = Category(name=category_data.name)
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def get_all_categories(db: Session) -> List[Category]:
        return db.query(Category).all()

    # --- PRODUCT SERVICES ---
    @staticmethod
    def create_product(db: Session, product_data: ProductCreate) -> Product:
        # Check SKU uniqueness
        existing_sku = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{product_data.sku}' already exists."
            )
        
        # Verify category exists
        category = db.query(Category).filter(Category.id == product_data.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        # Insert product
        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            category_id=product_data.category_id,
            sku=product_data.sku
        )
        db.add(product)
        db.flush()  # Generates product.id

        # Automatically create empty Inventory record
        inventory = Inventory(product_id=product.id, quantity=0, reserved_quantity=0, reorder_level=10)
        db.add(inventory)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Product not found."
            )
        return product

    @classmethod
    def update_product(cls, db: Session, product_id: int, product_data: ProductUpdate) -> Product:
        product = cls.get_product_by_id(db, product_id)

        # Validate SKU uniqueness if SKU is changing
        if product_data.sku and product_data.sku != product.sku:
            existing_sku = db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing_sku:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SKU '{product_data.sku}' already exists."
                )

        # Validate category if changing
        if product_data.category_id and product_data.category_id != product.category_id:
            category = db.query(Category).filter(Category.id == product_data.category_id).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found."
                )

        # Update fields dynamically
        for field, value in product_data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)
        return product

    @classmethod
    def delete_product(cls, db: Session, product_id: int) -> bool:
        product = cls.get_product_by_id(db, product_id)
        db.delete(product)
        db.commit()
        return True

    @staticmethod
    def get_products_filtered(
        db: Session,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "id",
        sort_order: str = "asc",
        page: int = 1,
        limit: int = 20
    ) -> List[Product]:
        """
        Builds a dynamic query applying search, filter, sorting, and pagination.
        - category: filter by category name
        - min_price / max_price: range filters
        - search: text matching name or description
        - sort_by: field name (id, price, name, etc.)
        - sort_order: asc or desc
        """
        query = db.query(Product)

        # 1. Join category table if category name is provided
        if category:
            query = query.join(Category).filter(Category.name.ilike(category))

        # 2. Price filtering
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # 3. Search matching name or description
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Product.name.ilike(search_pattern)) | 
                (Product.description.ilike(search_pattern))
            )

        # 4. Sorting logic
        sort_column = getattr(Product, sort_by, Product.id)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # 5. Pagination offset/limit
        offset = (page - 1) * limit
        return query.offset(offset).limit(limit).all()
