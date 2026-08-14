from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Text, Boolean, ForeignKey, func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    persona = Column(String(50), nullable=False)
    organization = Column(String(255), nullable=True)
    jurisdiction_scope = Column(String(255), default="Rewa District, Madhya Pradesh")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    geography_name = Column(String(255), default="Rewa District")
    bbox_min_lon = Column(Float, default=81.1)
    bbox_min_lat = Column(Float, default=24.4)
    bbox_max_lon = Column(Float, default=81.5)
    bbox_max_lat = Column(Float, default=24.8)
    permission_scope = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Rewa District")
    district = Column(String(100), default="Rewa")
    state = Column(String(100), default="Madhya Pradesh")
    bbox_min_lon = Column(Float, default=81.1)
    bbox_min_lat = Column(Float, default=24.4)
    bbox_max_lon = Column(Float, default=81.5)
    bbox_max_lat = Column(Float, default=24.8)
    geometry_wkt = Column(Text, nullable=True)
    geometry_geojson = Column(JSON, nullable=True)

class GraphNode(Base):
    __tablename__ = "graph_nodes"
    
    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    node_type = Column(String(50), nullable=False, index=True)  # PROBLEM, INTERVENTION, OUTPUT, CO_BENEFIT, DOMAIN
    domain = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    attributes_json = Column(JSON, nullable=True)

class GraphEdge(Base):
    __tablename__ = "graph_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(100), ForeignKey("graph_nodes.id"), nullable=False, index=True)
    target_id = Column(String(100), ForeignKey("graph_nodes.id"), nullable=False, index=True)
    edge_type = Column(String(50), nullable=False, index=True)  # ADDRESSES, PRODUCES, ENABLES, COMPATIBLE_WITH, DEPENDS_ON
    weight = Column(Float, default=1.0)
    attributes_json = Column(JSON, nullable=True)

class PortfolioRecord(Base):
    __tablename__ = "portfolio_records"
    
    id = Column(String(100), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    geography_id = Column(String(100), default="rewa")
    total_cost_inr = Column(Float, nullable=False)
    water_security_score = Column(Float, nullable=False)
    jobs_created = Column(Integer, nullable=False)
    sdg_count = Column(Integer, nullable=False)
    portfolio_json = Column(JSON, nullable=False)
    provenance_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
