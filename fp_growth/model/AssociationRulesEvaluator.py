import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Any

class AssociationRulesEvaluator:
    def __init__(self, rules_df: pd.DataFrame):
        """
        Khởi tạo evaluator với dataframe chứa luật kết hợp
        
        Parameters:
        -----------
        rules_df : pd.DataFrame
            DataFrame chứa các luật kết hợp với các cột:
            - antecedents, consequents: tập itemsets
            - antecedent_names, consequent_names: tên items
            - support, confidence, lift, conviction: các chỉ số
            - antecedent_len, consequent_len: độ dài itemsets
        """
        self.rules_df = rules_df.copy()
        
    def basic_statistics(self) -> Dict[str, Any]:
        """
        Tính toán các thống kê cơ bản về tập luật
        """
        stats = {
            'total_rules': len(self.rules_df),
            'avg_confidence': self.rules_df['confidence'].mean(),
            'avg_support': self.rules_df['support'].mean(),
            'avg_lift': self.rules_df['lift'].mean(),
            'avg_conviction': self.rules_df['conviction'].mean(),
            'max_confidence': self.rules_df['confidence'].max(),
            'min_confidence': self.rules_df['confidence'].min(),
            'max_lift': self.rules_df['lift'].max(),
            'min_lift': self.rules_df['lift'].min(),
            'rules_by_antecedent_len': self.rules_df['antecedent_len'].value_counts().to_dict(),
            'rules_by_consequent_len': self.rules_df['consequent_len'].value_counts().to_dict()
        }
        
        return stats
    
    def filter_rules_by_metrics(self, 
                               min_confidence: float = 0.7,
                               min_lift: float = 1.0,
                               min_support: float = 0.01,
                               max_antecedent_len: int = 5) -> pd.DataFrame:
        """
        Lọc luật dựa trên các ngưỡng chỉ số
        """
        filtered_df = self.rules_df[
            (self.rules_df['confidence'] >= min_confidence) &
            (self.rules_df['lift'] >= min_lift) &
            (self.rules_df['support'] >= min_support) &
            (self.rules_df['antecedent_len'] <= max_antecedent_len)
        ]
        
        print(f"Tổng số luật ban đầu: {len(self.rules_df)}")
        print(f"Số luật sau khi lọc: {len(filtered_df)}")
        print(f"Tỷ lệ giữ lại: {len(filtered_df)/len(self.rules_df)*100:.2f}%")
        
        return filtered_df
    
    def get_top_n_rules(self, 
                       n: int = 10, 
                       sort_by: str = 'lift',
                       ascending: bool = False) -> pd.DataFrame:
        """
        Lấy N luật tốt nhất theo chỉ số chỉ định
        """
        valid_columns = ['support', 'confidence', 'lift', 'conviction']
        if sort_by not in valid_columns:
            raise ValueError(f"sort_by phải là một trong {valid_columns}")
        
        return self.rules_df.sort_values(by=sort_by, ascending=ascending).head(n)
    
    def analyze_rule_patterns(self) -> Dict[str, Any]:
        """
        Phân tích các mẫu luật phổ biến
        """
        # Phân tích độ dài luật
        rule_lengths = self.rules_df['antecedent_len'] + self.rules_df['consequent_len']
        
        # Tìm các consequent phổ biến nhất
        consequent_counts = {}
        for consequent_set in self.rules_df['consequent_names']:
            for item in consequent_set:
                consequent_counts[item] = consequent_counts.get(item, 0) + 1
        
        # Tìm các antecedent phổ biến nhất
        antecedent_counts = {}
        for antecedent_set in self.rules_df['antecedent_names']:
            for item in antecedent_set:
                antecedent_counts[item] = antecedent_counts.get(item, 0) + 1
        
        analysis = {
            'avg_rule_length': rule_lengths.mean(),
            'min_rule_length': rule_lengths.min(),
            'max_rule_length': rule_lengths.max(),
            'top_10_consequents': sorted(consequent_counts.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:10],
            'top_10_antecedents': sorted(antecedent_counts.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:10]
        }
        
        return analysis
    
    def visualize_metrics(self, figsize: Tuple[int, int] = (15, 10)):
        """
        Trực quan hóa các chỉ số của luật
        """
        fig, axes = plt.subplots(2, 3, figsize=figsize)
        
        # 1. Histogram của confidence
        axes[0, 0].hist(self.rules_df['confidence'], bins=50, alpha=0.7, color='blue')
        axes[0, 0].set_xlabel('Confidence')
        axes[0, 0].set_ylabel('Số lượng luật')
        axes[0, 0].set_title('Phân bố Confidence')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Histogram của lift
        axes[0, 1].hist(self.rules_df['lift'], bins=50, alpha=0.7, color='green')
        axes[0, 1].set_xlabel('Lift')
        axes[0, 1].set_ylabel('Số lượng luật')
        axes[0, 1].set_title('Phân bố Lift')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Histogram của support
        axes[0, 2].hist(self.rules_df['support'], bins=50, alpha=0.7, color='red')
        axes[0, 2].set_xlabel('Support')
        axes[0, 2].set_ylabel('Số lượng luật')
        axes[0, 2].set_title('Phân bố Support')
        axes[0, 2].grid(True, alpha=0.3)
        
        # 4. Scatter plot: Confidence vs Lift
        axes[1, 0].scatter(self.rules_df['confidence'], 
                          self.rules_df['lift'], 
                          alpha=0.5, s=10)
        axes[1, 0].set_xlabel('Confidence')
        axes[1, 0].set_ylabel('Lift')
        axes[1, 0].set_title('Confidence vs Lift')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Scatter plot: Support vs Confidence
        axes[1, 1].scatter(self.rules_df['support'], 
                          self.rules_df['confidence'], 
                          alpha=0.5, s=10)
        axes[1, 1].set_xlabel('Support')
        axes[1, 1].set_ylabel('Confidence')
        axes[1, 1].set_title('Support vs Confidence')
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Bar plot: Số luật theo độ dài antecedent
        antecedent_len_counts = self.rules_df['antecedent_len'].value_counts().sort_index()
        axes[1, 2].bar(antecedent_len_counts.index, 
                      antecedent_len_counts.values, 
                      alpha=0.7, color='purple')
        axes[1, 2].set_xlabel('Độ dài Antecedent')
        axes[1, 2].set_ylabel('Số lượng luật')
        axes[1, 2].set_title('Phân bố độ dài Antecedent')
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Thêm heatmap correlation
        correlation_matrix = self.rules_df[['support', 'confidence', 'lift', 'conviction']].corr()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', 
                    center=0, ax=ax, fmt='.2f')
        ax.set_title('Ma trận tương quan giữa các chỉ số')
        plt.show()
    
    def evaluate_rule_quality(self) -> pd.DataFrame:
        """
        Đánh giá chất lượng luật bằng composite score
        """
        # Chuẩn hóa các chỉ số
        df = self.rules_df.copy()
        
        # Tính composite score (có thể điều chỉnh trọng số)
        df['composite_score'] = (
                0.3 * (df['confidence'] / df['confidence'].max()) +
                0.3 * (df['lift'] / df['lift'].max()) +
                0.2 * (df['support'] / df['support'].max()) +
                0.2 * (df['conviction'].clip(upper=10) / 10)  # Clip conviction để tránh infinity
        )
        
        # Phân loại luật - FIX: Sử dụng default parameter thay vì rely on implicit default
        def categorize_quality(score):
            if score >= 0.8:
                return 'Rất tốt'
            elif score >= 0.6:
                return 'Tốt'
            elif score >= 0.4:
                return 'Trung bình'
            else:
                return 'Kém'
        
        df['quality_category'] = df['composite_score'].apply(categorize_quality)
        
        return df
    
    def save_quality_report(self, output_path: str = 'rule_quality_report.xlsx'):
        """
        Lưu báo cáo đánh giá chất lượng luật
        """
        # Đánh giá chất lượng
        quality_df = self.evaluate_rule_quality()
        
        # Lấy thống kê
        stats = self.basic_statistics()
        patterns = self.analyze_rule_patterns()
        
        # Tạo writer cho Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Toàn bộ luật với chất lượng
            quality_df.to_excel(writer, sheet_name='All_Rules_with_Quality', index=False)
            
            # Sheet 2: Luật chất lượng cao
            high_quality = quality_df[quality_df['quality_category'].isin(['Rất tốt', 'Tốt'])]
            high_quality.to_excel(writer, sheet_name='High_Quality_Rules', index=False)
            
            # Sheet 3: Top 50 luật theo composite score
            top_50 = quality_df.sort_values('composite_score', ascending=False).head(50)
            top_50.to_excel(writer, sheet_name='Top_50_Rules', index=False)
            
            # Sheet 4: Thống kê tổng quan
            stats_df = pd.DataFrame([stats])
            patterns_df = pd.DataFrame([patterns])
            summary = pd.concat([stats_df, patterns_df], axis=1)
            summary.to_excel(writer, sheet_name='Summary_Statistics', index=False)
            
            # Sheet 5: Phân phối chất lượng
            quality_dist = quality_df['quality_category'].value_counts()
            quality_dist_df = pd.DataFrame({
                'Chất lượng': quality_dist.index,
                'Số lượng': quality_dist.values,
                'Tỷ lệ': quality_dist.values / len(quality_df) * 100
            })
            quality_dist_df.to_excel(writer, sheet_name='Quality_Distribution', index=False)
        
        print(f"Báo cáo đã được lưu tại: {output_path}")


def load_rules_from_csv(file_path: str) -> pd.DataFrame:
    """
    Tải dữ liệu luật từ file CSV
    
    Parameters:
    -----------
    file_path : str
        Đường dẫn đến file CSV
        
    Returns:
    --------
    pd.DataFrame
        DataFrame chứa các luật kết hợp
    """
    # Tải dữ liệu
    df = pd.read_csv(file_path)
    
    # Chuyển đổi các cột chứa tập hợp từ string sang set/list
    if 'antecedents' in df.columns:
        df['antecedents'] = df['antecedents'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    if 'consequents' in df.columns:
        df['consequents'] = df['consequents'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    if 'antecedent_names' in df.columns:
        df['antecedent_names'] = df['antecedent_names'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    if 'consequent_names' in df.columns:
        df['consequent_names'] = df['consequent_names'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    
    print(f"Đã tải {len(df)} luật từ {file_path}")
    print(f"Các cột có sẵn: {list(df.columns)}")
    
    return df


# Hàm main để chạy toàn bộ đánh giá
def evaluate_association_rules(csv_path: str, 
                             min_confidence: float = 0.7,
                             min_lift: float = 1.0,
                             min_support: float = 0.01,
                             generate_report: bool = True):
    """
    Hàm chính để đánh giá luật kết hợp từ file CSV
    """
    # 1. Tải dữ liệu
    print("=" * 50)
    print("BẮT ĐẦU ĐÁNH GIÁ LUẬT KẾT HỢP")
    print("=" * 50)
    
    rules_df = load_rules_from_csv(csv_path)
    
    # 2. Khởi tạo evaluator
    evaluator = AssociationRulesEvaluator(rules_df)
    
    # 3. Tính toán thống kê cơ bản
    print("\n1. THỐNG KÊ CƠ BẢN:")
    print("-" * 30)
    stats = evaluator.basic_statistics()
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            if 'avg' in key:
                print(f"{key}: {value:.4f}")
            else:
                print(f"{key}: {value}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for k, v in value.items():
                print(f"  - Độ dài {k}: {v} luật")
    
    # 4. Phân tích mẫu luật
    print("\n2. PHÂN TÍCH MẪU LUẬT:")
    print("-" * 30)
    patterns = evaluator.analyze_rule_patterns()
    print(f"Độ dài luật trung bình: {patterns['avg_rule_length']:.2f}")
    print(f"Độ dài luật nhỏ nhất: {patterns['min_rule_length']}")
    print(f"Độ dài luật lớn nhất: {patterns['max_rule_length']}")
    
    print("\n10 consequent phổ biến nhất:")
    for item, count in patterns['top_10_consequents']:
        print(f"  - {item}: {count} luật")
    
    print("\n10 antecedent phổ biến nhất:")
    for item, count in patterns['top_10_antecedents']:
        print(f"  - {item}: {count} luật")
    
    # 5. Lọc và hiển thị luật tốt nhất
    print("\n3. LUẬT CHẤT LƯỢNG CAO:")
    print("-" * 30)
    
    # Lọc luật
    filtered_rules = evaluator.filter_rules_by_metrics(
        min_confidence=min_confidence,
        min_lift=min_lift,
        min_support=min_support
    )
    
    # Top 10 luật theo lift
    print("\nTop 10 luật theo Lift:")
    top_lift = evaluator.get_top_n_rules(n=10, sort_by='lift')
    for idx, row in top_lift.iterrows():
        print(f"\nLuật #{idx}:")
        print(f"  Antecedent: {row['antecedent_names']}")
        print(f"  Consequent: {row['consequent_names']}")
        print(f"  Support: {row['support']:.4f}, Confidence: {row['confidence']:.4f}, "
              f"Lift: {row['lift']:.4f}")
    
    # Top 10 luật theo confidence
    print("\nTop 10 luật theo Confidence:")
    top_conf = evaluator.get_top_n_rules(n=10, sort_by='confidence')
    for idx, row in top_conf.iterrows():
        print(f"\nLuật #{idx}:")
        print(f"  Antecedent: {row['antecedent_names']}")
        print(f"  Consequent: {row['consequent_names']}")
        print(f"  Support: {row['support']:.4f}, Confidence: {row['confidence']:.4f}, "
              f"Lift: {row['lift']:.4f}")
    
    # 6. Trực quan hóa
    print("\n4. TRỰC QUAN HÓA DỮ LIỆU:")
    print("-" * 30)
    evaluator.visualize_metrics()
    
    # 7. Tạo báo cáo nếu được yêu cầu
    if generate_report:
        print("\n5. TẠO BÁO CÁO:")
        print("-" * 30)
        evaluator.save_quality_report()
    
    print("\n" + "=" * 50)
    print("KẾT THÚC ĐÁNH GIÁ")
    print("=" * 50)
    
    return evaluator


# Ví dụ sử dụng
if __name__ == "__main__":
    # Thay đổi đường dẫn đến file CSV của bạn
    CSV_FILE_PATH = "D:\\ProjectFITHAU\\music-recommendation-system-dmn\\fp_growth\\model\\rules_track.csv"  # Thay bằng đường dẫn thực tế
    
    try:
        # Chạy đánh giá
        evaluator = evaluate_association_rules(
            csv_path=CSV_FILE_PATH,
            min_confidence=0.7,      # Ngưỡng confidence tối thiểu
            min_lift=1.2,           # Ngưỡng lift tối thiểu (>1 thể hiện mối quan hệ tích cực)
            min_support=0.01,       # Ngưỡng support tối thiểu
            generate_report=True    # Tạo file báo cáo Excel
        )
        
    except FileNotFoundError:
        print(f"Không tìm thấy file: {CSV_FILE_PATH}")
        print("Vui lòng kiểm tra đường dẫn file CSV.")
    except Exception as e:
        print(f"Có lỗi xảy ra: {str(e)}")