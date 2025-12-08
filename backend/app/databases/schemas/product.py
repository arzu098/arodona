from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

# Jewelry-specific enums
class JewelryType(str, Enum):
    """Enum for jewelry types"""
    RING = "ring"
    NECKLACE = "necklace"
    EARRINGS = "earrings"
    BRACELET = "bracelet"
    PENDANT = "pendant"
    BROOCH = "brooch"
    WATCH = "watch"
    ANKLET = "anklet"
    CHAIN = "chain"
    CHARM = "charm"
    CUFFLINKS = "cufflinks"
    TIARA = "tiara"
    OTHER = "other"

class MetalType(str, Enum):
    """Enum for metal types"""
    GOLD_14K = "14k_gold"
    GOLD_18K = "18k_gold"
    GOLD_22K = "22k_gold"
    GOLD_24K = "24k_gold"
    WHITE_GOLD = "white_gold"
    ROSE_GOLD = "rose_gold"
    SILVER = "silver"
    STERLING_SILVER = "sterling_silver"
    PLATINUM = "platinum"
    PALLADIUM = "palladium"
    TITANIUM = "titanium"
    STAINLESS_STEEL = "stainless_steel"
    COPPER = "copper"
    BRASS = "brass"
    OTHER = "other"

class GemstoneType(str, Enum):
    """Enum for gemstone types"""
    DIAMOND = "diamond"
    EMERALD = "emerald"
    RUBY = "ruby"
    SAPPHIRE = "sapphire"
    PEARL = "pearl"
    AMETHYST = "amethyst"
    AQUAMARINE = "aquamarine"
    CITRINE = "citrine"
    GARNET = "garnet"
    OPAL = "opal"
    PERIDOT = "peridot"
    TOPAZ = "topaz"
    TURQUOISE = "turquoise"
    ONYX = "onyx"
    JADE = "jade"
    CORAL = "coral"
    MOONSTONE = "moonstone"
    TANZANITE = "tanzanite"
    CUBIC_ZIRCONIA = "cubic_zirconia"
    SYNTHETIC = "synthetic"
    OTHER = "other"

class DiamondCut(str, Enum):
    """Enum for diamond cuts"""
    ROUND = "round"
    PRINCESS = "princess"
    EMERALD = "emerald"
    ASSCHER = "asscher"
    OVAL = "oval"
    RADIANT = "radiant"
    CUSHION = "cushion"
    MARQUISE = "marquise"
    PEAR = "pear"
    HEART = "heart"
    BAGUETTE = "baguette"

class DiamondClarity(str, Enum):
    """Enum for diamond clarity grades"""
    FL = "fl"  # Flawless
    IF = "if"  # Internally Flawless
    VVS1 = "vvs1"  # Very Very Slightly Included 1
    VVS2 = "vvs2"  # Very Very Slightly Included 2
    VS1 = "vs1"   # Very Slightly Included 1
    VS2 = "vs2"   # Very Slightly Included 2
    SI1 = "si1"   # Slightly Included 1
    SI2 = "si2"   # Slightly Included 2
    I1 = "i1"     # Included 1
    I2 = "i2"     # Included 2
    I3 = "i3"     # Included 3

class DiamondColor(str, Enum):
    """Enum for diamond color grades"""
    D = "d"  # Colorless
    E = "e"
    F = "f"
    G = "g"  # Near Colorless
    H = "h"
    I = "i"
    J = "j"
    K = "k"  # Faint Yellow
    L = "l"
    M = "m"

class ProductStatus(str, Enum):
    """Enum for product status"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class ProductCondition(str, Enum):
    """Enum for product condition"""
    NEW = "new"
    LIKE_NEW = "like_new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    VINTAGE = "vintage"
    ANTIQUE = "antique"

# Jewelry-specific schemas
class GemstoneInfo(BaseModel):
    """Schema for gemstone information"""
    type: GemstoneType
    carat_weight: Optional[float] = Field(None, gt=0, description="Carat weight of the gemstone")
    cut: Optional[DiamondCut] = None  # Applicable for diamonds and some other gems
    clarity: Optional[DiamondClarity] = None  # Applicable for diamonds
    color: Optional[DiamondColor] = None  # Applicable for diamonds
    origin: Optional[str] = Field(None, max_length=100, description="Country or region of origin")
    certification: Optional[str] = Field(None, max_length=200, description="Certification details (GIA, AGS, etc.)")
    treatment: Optional[str] = Field(None, max_length=200, description="Any treatments applied")
    shape: Optional[str] = Field(None, max_length=50, description="Shape of the gemstone")
    quantity: int = Field(1, ge=1, description="Number of this gemstone in the product")

class ProductDimensions(BaseModel):
    """Schema for product dimensions"""
    length: Optional[float] = Field(None, gt=0, description="Length in mm")
    width: Optional[float] = Field(None, gt=0, description="Width in mm")
    height: Optional[float] = Field(None, gt=0, description="Height in mm")
    diameter: Optional[float] = Field(None, gt=0, description="Diameter in mm (for round items)")
    chain_length: Optional[float] = Field(None, gt=0, description="Chain length in cm")

class ProductWeight(BaseModel):
    """Schema for product weight"""
    total_weight: Optional[float] = Field(None, gt=0, description="Total weight in grams")
    metal_weight: Optional[float] = Field(None, gt=0, description="Metal weight in grams")
    gemstone_weight: Optional[float] = Field(None, gt=0, description="Total gemstone weight in carats")

class SizeVariation(BaseModel):
    """Schema for size variations"""
    size: str = Field(..., description="Size identifier (e.g., '7', 'M', '16 inches')")
    size_type: str = Field(..., description="Type of size (ring, bracelet, necklace, etc.)")
    sku: Optional[str] = Field(None, description="Unique SKU for this size variation")
    price_adjustment: Optional[float] = Field(0, description="Price adjustment for this size")
    stock_quantity: int = Field(0, ge=0, description="Available stock for this size")
    is_available: bool = Field(True, description="Whether this size is currently available")

class ProductVariant(BaseModel):
    """Schema for product variants (color, material, etc.)"""
    name: str = Field(..., max_length=100, description="Variant name")
    type: str = Field(..., max_length=50, description="Variant type (color, metal, finish, etc.)")
    value: str = Field(..., max_length=100, description="Variant value")
    sku: Optional[str] = Field(None, description="Unique SKU for this variant")
    price_adjustment: Optional[float] = Field(0, description="Price adjustment for this variant")
    stock_quantity: int = Field(0, ge=0, description="Available stock for this variant")
    images: Optional[List[str]] = Field(None, description="Variant-specific images")

class ProductImage(BaseModel):
    """Schema for product images"""
    url: str = Field(..., description="Image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    alt_text: Optional[str] = Field(None, max_length=200, description="Alt text for accessibility")
    is_primary: bool = Field(False, description="Whether this is the primary image")
    sort_order: int = Field(0, description="Sort order for image display")
    variant_id: Optional[str] = Field(None, description="Associated variant ID if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "/uploads/products/vendor123/product456/image.jpg",
                "thumbnail_url": "/uploads/products/vendor123/product456/image_thumb.jpg",
                "alt_text": "Product Image",
                "is_primary": True,
                "sort_order": 0
            }
        }

class SEOInfo(BaseModel):
    """Schema for SEO information"""
    meta_title: Optional[str] = Field(None, max_length=60, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=160, description="SEO meta description")
    keywords: Optional[List[str]] = Field(None, description="SEO keywords")
    slug: Optional[str] = Field(None, max_length=200, description="URL slug")

class ProductCreate(BaseModel):
    """Schema for creating a jewelry product"""
    # Basic product information
    name: str = Field(..., min_length=2, max_length=200, description="Product name")
    description: str = Field(..., min_length=10, max_length=2000, description="Product description")
    short_description: Optional[str] = Field(None, max_length=300, description="Short product description")
    price: float = Field(..., gt=0, description="Product price")
    compare_at_price: Optional[float] = Field(None, gt=0, description="Original price for comparison")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price for vendor")
    
    # Jewelry-specific attributes
    jewelry_type: JewelryType = Field(..., description="Type of jewelry")
    metal_type: MetalType = Field(..., description="Primary metal type")
    metal_purity: Optional[str] = Field(None, max_length=50, description="Metal purity (e.g., 14k, 925)")
    gemstones: Optional[List[GemstoneInfo]] = Field(None, description="Gemstone information")
    
    # Physical attributes
    dimensions: Optional[ProductDimensions] = Field(None, description="Product dimensions")
    weight: Optional[ProductWeight] = Field(None, description="Product weight information")
    
    # Product variations
    sizes: Optional[List[SizeVariation]] = Field(None, description="Available sizes")
    variants: Optional[List[ProductVariant]] = Field(None, description="Product variants (colors, finishes, etc.)")
    
    # Inventory and pricing
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    stock_quantity: int = Field(0, ge=0, description="Available stock quantity")
    low_stock_threshold: Optional[int] = Field(5, ge=0, description="Low stock alert threshold")
    track_inventory: bool = Field(True, description="Whether to track inventory for this product")
    
    # Categorization and organization
    categories: Optional[List[str]] = Field(None, description="Category IDs or slugs")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    brand: Optional[str] = Field(None, max_length=100, description="Brand name")
    collection: Optional[str] = Field(None, max_length=100, description="Collection name")
    
    # Product status and condition
    status: ProductStatus = Field(ProductStatus.DRAFT, description="Product status")
    condition: ProductCondition = Field(ProductCondition.NEW, description="Product condition")
    
    # Media
    images: Optional[List[ProductImage]] = Field(None, description="Product images")
    
    # SEO and marketing
    seo: Optional[SEOInfo] = Field(None, description="SEO information")
    featured: bool = Field(False, description="Whether product is featured")
    
    # Additional attributes
    care_instructions: Optional[str] = Field(None, max_length=1000, description="Care and maintenance instructions")
    materials: Optional[List[str]] = Field(None, description="Additional materials used")
    origin_country: Optional[str] = Field(None, max_length=100, description="Country of origin/manufacture")
    warranty_info: Optional[str] = Field(None, max_length=500, description="Warranty information")
    custom_attributes: Optional[Dict[str, Any]] = Field(None, description="Custom product attributes")
    
    @validator('price', 'compare_at_price', 'cost_price')
    def validate_prices(cls, v):
        if v is not None and v < 0:
            raise ValueError('Prices must be non-negative')
        return v
    
    @validator('compare_at_price')
    def validate_compare_at_price(cls, v, values):
        if v is not None and 'price' in values and v <= values['price']:
            raise ValueError('Compare at price must be higher than selling price')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Diamond Engagement Ring",
                "description": "Beautiful solitaire diamond engagement ring crafted in 18k white gold",
                "short_description": "Elegant solitaire diamond ring in 18k white gold",
                "price": 2500.00,
                "compare_at_price": 3000.00,
                "jewelry_type": "ring",
                "metal_type": "white_gold",
                "metal_purity": "18k",
                "gemstones": [
                    {
                        "type": "diamond",
                        "carat_weight": 1.0,
                        "cut": "round",
                        "clarity": "vs1",
                        "color": "g",
                        "certification": "GIA Certified"
                    }
                ],
                "dimensions": {
                    "diameter": 15.0,
                    "height": 8.0
                },
                "weight": {
                    "total_weight": 4.5,
                    "metal_weight": 3.5,
                    "gemstone_weight": 1.0
                },
                "sizes": [
                    {
                        "size": "6",
                        "size_type": "ring",
                        "stock_quantity": 2
                    },
                    {
                        "size": "7",
                        "size_type": "ring",
                        "stock_quantity": 3
                    }
                ],
                "sku": "DR001-WG-1CT",
                "stock_quantity": 5,
                "categories": ["engagement-rings", "diamond-jewelry"],
                "tags": ["diamond", "engagement", "solitaire", "white-gold"],
                "brand": "Elegant Designs",
                "status": "active",
                "condition": "new"
            }
        }

class ProductUpdate(BaseModel):
    """Schema for updating a jewelry product"""
    # Basic product information
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    short_description: Optional[str] = Field(None, max_length=300)
    price: Optional[float] = Field(None, gt=0)
    compare_at_price: Optional[float] = Field(None, gt=0)
    cost_price: Optional[float] = Field(None, ge=0)
    
    # Jewelry-specific attributes
    jewelry_type: Optional[JewelryType] = None
    metal_type: Optional[MetalType] = None
    metal_purity: Optional[str] = Field(None, max_length=50)
    gemstones: Optional[List[GemstoneInfo]] = None
    
    # Physical attributes
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[ProductWeight] = None
    
    # Product variations
    sizes: Optional[List[SizeVariation]] = None
    variants: Optional[List[ProductVariant]] = None
    
    # Inventory and pricing
    sku: Optional[str] = Field(None, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    track_inventory: Optional[bool] = None
    
    # Categorization and organization
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    brand: Optional[str] = Field(None, max_length=100)
    collection: Optional[str] = Field(None, max_length=100)
    
    # Product status and condition
    status: Optional[ProductStatus] = None
    condition: Optional[ProductCondition] = None
    
    # Media
    images: Optional[List[ProductImage]] = None
    
    # SEO and marketing
    seo: Optional[SEOInfo] = None
    featured: Optional[bool] = None
    
    # Additional attributes
    care_instructions: Optional[str] = Field(None, max_length=1000)
    materials: Optional[List[str]] = None
    origin_country: Optional[str] = Field(None, max_length=100)
    warranty_info: Optional[str] = Field(None, max_length=500)
    custom_attributes: Optional[Dict[str, Any]] = None
    
    @validator('price', 'compare_at_price', 'cost_price')
    def validate_prices(cls, v):
        if v is not None and v < 0:
            raise ValueError('Prices must be non-negative')
        return v

class CategoryInfo(BaseModel):
    """Category information in product response"""
    id: str
    name: str
    slug: str

class ProductResponse(BaseModel):
    """Schema for comprehensive product response"""
    # Basic information
    id: str
    vendor_id: str
    name: str
    description: str
    short_description: Optional[str] = None
    price: float
    compare_at_price: Optional[float] = None
    cost_price: Optional[float] = None
    
    # Jewelry-specific attributes
    jewelry_type: JewelryType
    metal_type: Optional[MetalType] = None
    metal_purity: Optional[str] = None
    gemstones: Optional[List[GemstoneInfo]] = None
    
    # Physical attributes
    dimensions: Optional[ProductDimensions] = None
    weight: Optional[ProductWeight] = None
    
    # Product variations
    sizes: Optional[List[SizeVariation]] = None
    variants: Optional[List[ProductVariant]] = None
    
    # Inventory and pricing
    sku: Optional[str] = None
    stock_quantity: int = 0
    stock: Optional[int] = None  # Backward compatibility alias for stock_quantity
    low_stock_threshold: Optional[int] = 5
    track_inventory: bool = True
    is_in_stock: bool = True
    is_active: Optional[bool] = True  # Backward compatibility for product active status
    
    # Categorization
    category: Optional[str] = None  # Single category (primary)
    categories: Optional[List[CategoryInfo]] = None
    tags: Optional[List[str]] = None
    brand: Optional[str] = None
    collection: Optional[str] = None
    
    # Product status
    status: ProductStatus
    condition: ProductCondition
    
    # Media
    images: Optional[List[ProductImage]] = None
    
    # SEO and marketing
    seo: Optional[SEOInfo] = None
    featured: bool = False
    
    # Ratings and reviews
    rating_avg: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    ratings_breakdown: Optional[Dict[str, int]] = None
    
    # Additional information
    care_instructions: Optional[str] = None
    materials: Optional[List[str]] = None
    origin_country: Optional[str] = None
    warranty_info: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    
    # Metadata
    view_count: Optional[int] = 0
    favorite_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
    
    # Backward compatibility
    category: Optional[str] = None  # Deprecated: use categories instead
    original_price: Optional[float] = None  # Deprecated: use compare_at_price instead
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ProductCreateResponse(BaseModel):
    """Schema for product creation response"""
    message: str
    product: ProductResponse

class ProductListResponse(BaseModel):
    """Schema for product list response"""
    total: int
    skip: int
    limit: int
    products: List[ProductResponse]

class ProductDeleteResponse(BaseModel):
    """Schema for product deletion response"""
    message: str
    product_id: str


class ProductSearchRequest(BaseModel):
    """Schema for product search request"""
    query: str
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    skip: int = 0
    limit: int = 10


class ProductBulkUpload(BaseModel):
    """Schema for bulk product upload"""
    products: List[ProductCreate]


class ProductInventoryUpdate(BaseModel):
    """Schema for updating product inventory"""
    sku: str
    quantity: int
    reserved_quantity: Optional[int] = 0


class ProductPricingTier(BaseModel):
    """Schema for product pricing tiers"""
    tier_name: str
    min_quantity: int
    price: float
    description: Optional[str] = None


class ProductTag(BaseModel):
    """Schema for product tags"""
    name: str
    slug: str
    description: Optional[str] = None


class CollectionCreate(BaseModel):
    """Schema for creating a product collection"""
    name: str
    slug: str
    description: Optional[str] = None
    product_ids: List[str] = []
    metadata: Optional[Dict] = None


class CollectionUpdate(BaseModel):
    """Schema for updating a product collection"""
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    product_ids: Optional[List[str]] = None
    metadata: Optional[Dict] = None


class CollectionResponse(BaseModel):
    """Schema for collection response"""
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    product_ids: List[str]
    metadata: Optional[Dict] = None
    created_at: datetime
    updated_at: datetime
